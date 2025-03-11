import { Injectable } from '@nestjs/common';
import * as dotenv from "dotenv";
import OpenAI from "openai";
import {AIMessage, createAIPrompt, createSystemPrompt} from "./utils";
import { Memory } from "./memory";
import {ConversationAgent} from "./conversation.agent";
import {UserService} from "../db/user.service";
import {FeedbackAgent} from "./feedback.agent";
import {User} from "../db/user.schema";

dotenv.config();

@Injectable()
export class ControllerAgent {
  private readonly modelName = "gpt-4o-mini";
  private readonly model: OpenAI;

  private readonly memory: Memory;

  constructor(
    private readonly userService: UserService,
    private readonly conversationAgent: ConversationAgent,
    private readonly feedbackAgent: FeedbackAgent,
  ) {
    this.model = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
    this.memory = new Memory(2);
  }

  async onboardUser(userId: string | null, input: { input: string }) {
    const user = await this.userService.getUser(userId);

    if (this.needsTutoringInformation(user)) {
      console.log('Configuration needs to happen to start Tutoring session (language and level)')
      const response = await this.conversationAgent.onboardUser(
        user,
        input.input,
      );
      return { userId: user._id.toString(), message: response };
    }
    return null;
  }

  private needsTutoringInformation<U>(user) {
    return (
      !user.language ||
      user.language.toLowerCase() === "unknown" ||
      !user.level ||
      user.level.toLowerCase() === "unknown"
    );
  }

  async processUserInput(userId: string, input: string) {
    const user = await this.userService.getUser(userId);
    const feedbackForUser = await this.feedbackAgent.isUserFollowingLesson(user, input)
    if( feedbackForUser ) return feedbackForUser;

    let aiGuidance: string | null = null
    let response: AIMessage | null = null;
    do {
      response = await this.conversationAgent.processUserInput(
        user,
        input,
        aiGuidance
      );

      aiGuidance = await this.feedbackAgent.isAIOnTopicAndLevel(user, response)
      if( aiGuidance !== null ) {
        await this.userService.removeLastInteraction(user)
      }
    }while(aiGuidance !== null);

    // yes -> Is user ready for exercise  (exercise agent)
    //        yes -> give exercise
    //        no -> conversation continues
    //           -> is AI on user Level  (feedback)
    //           yes -> return response
    //           no -> direct AI to stay on user level
    // not -> ask user to continue the lesson
    return response;
  }

  processAIInput(userId: string, input: string): any {
   // this.memory.addToMemory(userId, createAIPrompt(input));
  }

  private async isCreatingNewTutorSession(userId: string): Promise<boolean> {
    const prompt =
      createSystemPrompt(`Analyse the last interaction input and determine the action flow.
      Last Interaction: 
      ${this.memory.getRecentMemory(userId)}
      
      Required Answer are :
      - yes ( the most recent user message suggest the tutor needs to be restarted. )
      - no ( any other situation ) 
      `);

    const response = await this.invoke([prompt]);
    return response === "yes";
  }

  private async invoke(prompt: AIMessage[]) {
    const response = await this.model.chat.completions.create({
      model: this.modelName,
      messages: prompt,
    });
    return response.choices[0].message.content;
  }

}

