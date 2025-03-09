import { Injectable } from '@nestjs/common';
import * as dotenv from "dotenv";
import {ChatOpenAI} from "@langchain/openai";
import {ConversationChain} from "langchain/chains";
import { PromptTemplate } from "@langchain/core/prompts";
import {BufferMemory} from "langchain/memory";
import OpenAI from "openai";
import axios from "axios";


dotenv.config();

@Injectable()
export class AppService {

  private readonly model: ChatOpenAI;
  private readonly prompt;
  constructor() {
    this.model = new ChatOpenAI({
      apiKey: process.env.OPENAI_API_KEY,
      model: "gpt-4o-mini",
    });
    this.prompt = PromptTemplate.fromTemplate(`
        You are a friendly language tutor. Your goal is to help the user learn through natural conversation, asking follow-up questions, providing corrections, and adapting based on their skill level.
        The primary language is assumed to be english.
        Start by asking which language they want to learn, and their skill level.
        Tailor your answers based on the skill of the user.
        When the user makes a mistake, gently correct them and explain why. Encourage them to respond in the chosen language as much as possible. Keep your responses short to maintain a natural conversation.
        
        Example conversation:
        User: How do I say « I love pizza » in French  
        Tutor: On dit « J'adore la pizza. » Essaie de l’utiliser dans une phrase !
        User: « J'adore la pizza et les pâtes. »  
        Tutor: Perfect ! You said it correctly!. Want to learn how to say « I also love pasta » ?
        
        Example conversation:
        User: Bonjour comment va va?  
        Tutor: Très bien merci et toi?
        User: Je vais bien merci.  
        Tutor: Very good, let's continue... Quelle température fait-il chez toi?
        
        Now continue the conversation based on the user's input.
      
      Current conversation:
      {chat_history}
      User: {input}
      Tutor:
    `);


  }

  async textToSpeech(text: string) {
    const url = "https://api.openai.com/v1/audio/speech";
    const headers = {
      Authorization: `Bearer ${process.env.OPENAI_API_KEY}`, // API key for authentication
    };
    const data = {
      model: "tts-1",
      input: text,
      voice: "echo",
      response_format: "mp3",
    };
    try {
      // Make a POST request to the OpenAI audio API
      const response = await axios.post(url, data, {
        headers: headers,
        responseType: "arraybuffer"
      });
      return response.data.toString('base64');
    } catch (error) {
      // Handle errors from the API or the audio processing
      if (error.response) {
        console.error(
          `Error with HTTP request: ${error.response.status} - ${error.response.statusText}`
        );
      } else {
        console.error(`Error in streamedAudio: ${error.message}`);
      }
    }
  }

  async chat(userInput: { input }, previousMemory) {
    const memory = new BufferMemory({ memoryKey: "chat_history" });
    this.loadHistory(previousMemory, memory);
    const chain = new ConversationChain({
      llm: this.model,
      memory: memory,
      prompt: this.prompt
    });

    const response = await chain.call({ input: userInput });
    const voiceResponse = await this.textToSpeech(response.response);
    const thisChat: any[] = [];
    if( userInput.input !== 'init' ){
      thisChat.push(    {
        role: memory.humanPrefix,
        message: userInput.input
      })
    }
    thisChat.push({
        role: memory.aiPrefix,
        message: response.response,
        voice: voiceResponse
      }
    );

    return thisChat;
  }

  private loadHistory(previousMemory: any[], memory: BufferMemory) {
    previousMemory.forEach(memoryItem => {
      if( memoryItem.role === memory.humanPrefix) {
        return memory.chatHistory.addUserMessage(memoryItem.message)
      }
      memory.chatHistory.addAIChatMessage(memoryItem.message)
    })
  }
}
