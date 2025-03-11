import {AIMessage} from "./utils";
import {UserModel} from "../db/mongo.db";
import {Types} from "mongoose";

export class Memory {

  private readonly maxMemory: number;

  constructor(maxMemory: number) {
    this.maxMemory = maxMemory;
  }

  async addToMemory(userId: string, entry: AIMessage) {
    await UserModel().findByIdAndUpdate(userId, {$push: {memory: entry}});
  }

  async getRecentMemory(userId: string): Promise<AIMessage[]> {
    const mem = await this.getAllMemory(userId);
    return mem.slice(mem.length - this.maxMemory);
  }

  async getAllMemory(userId: string): Promise<AIMessage[]> {
    const response = await UserModel().findById(new Types.ObjectId(userId));
    return response!.history;
  }

}