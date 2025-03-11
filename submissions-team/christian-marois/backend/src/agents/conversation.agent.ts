import OpenAI from "openai";
import {Injectable} from "@nestjs/common";
import {AgentRole, AIMessage, createAIPrompt, createSystemPrompt, createUserPrompt, parseJSON} from "./utils";
import {User} from "../db/user.schema";
import {UserService} from "../db/user.service";
import * as _ from 'lodash';

@Injectable()
export class ConversationAgent {
  private readonly HISTORY_RETAINER = 20;

  private readonly modelName = 'gpt-4o-mini';
  private readonly model: OpenAI;

  constructor(private readonly userService: UserService,) {
    this.model = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
  }

  async onboardUser(user: User, input: string) {
    if (input === '') {
      const prompt = createSystemPrompt(`
      Ask the user what language he wishes to learn and what is his skill level in that language. 
      Levels are beginner, intermediate or advanced only.
        What is known so far is 
        Language to learn: ${user.language || 'unknown'}
        Skill level: ${user.level} || 'unknown'`);
      const response = await this.invoke([prompt])
      console.log('Initial setup asking user for language and level');

      await this.userService.addToMemory(user, createAIPrompt(AgentRole.SETUP, response!))
      return response;
    }
    await this.userService.addToMemory(user, createUserPrompt(AgentRole.SETUP, input))

    const prompt = createSystemPrompt(`
      # Analyze user input:
          
      User Input: ${input}
      
      ## What is known so far is 
      Language: ${user.language || 'unknown'}
      Skill: ${user.level} || 'unknown'
      
      ##The only acceptable response is the following JSON schema:
      ### JSON Schema:
      \`\`\`json
      { 
        "language": "The language the user entered in his response.",
        "level": "The level the user entered in his response.",
        "additional_response": "if language or level is missing from the response and it is unknown, the response back to ask for the missing information. Otherwise null"
      }
      \`\`\`
       
      `);
    const response = await this.invoke([prompt])

    const struct = parseJSON(response!);
    await this.userService.setTutoringInfo(user, struct.language, struct.level);
    console.log('User answered the following: '+struct.language + ' '+struct.level);

    if (struct.additional_response || struct.additional_response === 'null') {
      console.log('User did not fully answer replying with : '+struct.additional_response);
      await this.userService.addToMemory(user, createAIPrompt(AgentRole.SETUP, struct.additional_response))
    }
    return struct.additional_response;
  }

  async processUserInput(user: User, input: string, aiGuidance?: string|null) {
    let userPrompt: AIMessage | null = null;
    if (input !== '') {
      userPrompt = createUserPrompt(AgentRole.CONVERSATION, input);
      await this.userService.addToMemory(user, userPrompt);
    }

    const prompt = createSystemPrompt(`
        You are a friendly language tutor. 
        - Your goal is to help the user learn ${user.language} through natural conversation that will be stored in the 'message' field of the response.
        - Asking follow-up questions
        - Providing corrections
        - Adapting based on their skill level (${user.level}).
        - When the user makes a mistake, gently correct them and explain why. Encourage them to respond in ${user.language} as much as possible. 
        - Keep your responses short to maintain a natural conversation.
        - At Beginner level, speak to the user in english.
        - At Higher levels, you can immerse the user more in ${user.language}
        ${aiGuidance?'- Additional AI Guidance: '+aiGuidance: ''}
    
        ### Example Conversations:
        #### Beginner Example:
        {assistant} Can you tell me how to say hello in french?
        {user}      Bonjour  
        {assistant} Perfect ! You said it correctly!. Now follow up with "how are you?"
        
        #### Intermediate Example:
        {assistant} Peux-tu me dire ce que tu as fais aujourd'hui?
        {user}      Je suis allé au cinéma.  
        {assistant} Bien! Et quel film as tu été voir?
        
        Now continue the conversation based on the user's input.
      
      ### Already Covered topics:
      ${_.flattenDepth(user.topics_covered, 3)}
      
      ### Recent messages:
      ${this.getLastConversations(user).map(msg => `${msg.role}: ${msg.content}`).join('\n\n')}
      
      ### Current conversation:  (if user input is blank, start the conversation)
      User: ${input}
    `);
    const prompts: AIMessage[] = []
    prompts.push(prompt,  ...this.getLastConversations(user));
    if( userPrompt ) prompts.push(userPrompt);
    console.log('Conversing with user');
    const response = await this.invoke(prompts);
    const topics = await this.getTopics(user.language, input);
    console.log("Topics extracted from the user's last message are: "+ topics);
    const message = createAIPrompt(AgentRole.CONVERSATION, response!)
    await this.userService.addToMemory(user, message);
    await this.userService.addToTopics(user, topics!);
    return message;
  }

  private async getTopics(lang: string, text: string) {
    return this.invoke([createSystemPrompt(`
      # List the main words covered in ${lang} in the following text: 
      ${text}
        
      #The only acceptable response is a comma separated list of words with no other explanation`)]);
  }

  private async invoke(prompt: AIMessage[]) {
    const response =  await this.model.chat.completions.create({
      model: this.modelName,
      messages: prompt,
    })
    return response.choices[0].message.content;
  }

  private getLastConversations(user: User): AIMessage[] {
    return user.history.filter(h => h.agent === AgentRole.CONVERSATION).slice(user.history.length - this.HISTORY_RETAINER)
  }
}