import { Injectable } from "@nestjs/common";
import * as dotenv from "dotenv";
import OpenAI from "openai";
import {
  AgentRole,
  AIMessage,
  createAIPrompt,
  createSystemPrompt,
  Role,
} from "./utils";
import { Memory } from "./memory";
import { ConversationAgent } from "./conversation.agent";
import { UserService } from "../db/user.service";
import { User } from "../db/user.schema";

dotenv.config();

@Injectable()
export class FeedbackAgent {
  private readonly modelName = "gpt-4o-mini";
  private readonly model: OpenAI;

  private readonly memory: Memory;

  constructor(
    private readonly userService: UserService,
    private readonly conversationAgent: ConversationAgent,
  ) {
    this.model = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
    this.memory = new Memory(2);
  }

  async analyzeUserInput(userId: string, input: string) {
    const user = await this.userService.getUser(userId);
    const response = await this.conversationAgent.processUserInput(user, input);
    return response;
  }

  processAIInput(userId: string, input: string): any {
    // this.memory.addToMemory(userId, createAIPrompt(input));
  }

  async isUserFollowingLesson(user: User, input: string) {
    const lastAIMsg = this.userService.getLastAIConversation(user);
    if( !lastAIMsg || input === '' ) return null;
    const response = await this.invoke([
      createSystemPrompt(`
      # Given the conversation below:
      ${lastAIMsg.role}: ${lastAIMsg.content}
       
      ${Role.USER}: ${input}
        
      ## Is the user responding to the ${lastAIMsg.role} message?
      
      ### Acceptable answers: 
      If the user is following the conversation, answer with only 'yes'.
      If the user is asking for help, answer with only 'yes'.
      If the user is not following the conversation, respond politely to the user to follow the conversation 
      
      Example of Yes:
      assistant: Can you say Hello in French
      user: Bonjour
      feedback agent: 'yes'  
      
      Example of No:
      assistant: Can you say Hello in French
      user: Let's party!
      feedback agent: Please follow the conversation and reply according to what is asked.
      `),
    ]);
    console.log('Feedback agent is verifying if user is staying on topic,  response is: '+ response);

    if (response!.includes("yes")) {
      return null;
    }
    const message = createAIPrompt(AgentRole.FEEDBACK, response!);
    this.userService.addToMemory(user, message);
    return message;
  }

  async isAIOnTopicAndLevel(user: User, message: AIMessage) {
    const response = await this.invoke([
      createSystemPrompt(`
      # Given the text below:
      ${message.role}: ${message.content}
       
      ## Is the text in line with the following requirements:
      - Needs to be tutoring ${user.language} to the user.
      - Needs to be at the aimed at ${user.level} level.
      
      ### Acceptable answers: 
      If the text fulfills the requirements, answer with only 'yes'.
      If the text does not fulfill the requirements, response with 'System' prompt instructions to guide the AI to give a good response.  
      `),
    ]);
    console.log('Feedback agent is verifying if AI is following lesson for user,  response is: '+ response);
    if (response!.includes("yes")) {
      return null;
    }
    return response;

  }

  private async invoke(prompt: AIMessage[]) {
    const response = await this.model.chat.completions.create({
      model: this.modelName,
      messages: prompt,
    });
    return response.choices[0].message.content;
  }
}
