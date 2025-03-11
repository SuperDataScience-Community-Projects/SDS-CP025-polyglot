import { Injectable } from "@nestjs/common";
import { UserModel } from "./mongo.db";
import { Types } from "mongoose";
import { User } from "./user.schema";
import { AgentRole, AIMessage, Role } from "../agents/utils";
import * as _ from "lodash";

@Injectable()
export class UserService {
  async getUser(userId: string | null) {
    if (!userId) return UserModel().create({});
    const user = await UserModel().findById(new Types.ObjectId(userId));
    if (!user) return UserModel().create({});
    return user;
  }

  async setTutoringInfo(user: User, language: string, level: string) {
    await UserModel().findByIdAndUpdate(user._id, { language, level }).exec();
  }

  async addToMemory(user: User, aiMessage: AIMessage) {
    await UserModel()
      .findByIdAndUpdate(user._id, { $push: { history: aiMessage } })
      .exec();
  }

  async addToTopics(user: User, topics: string | string[]) {
    if (topics.length) {
      await UserModel()
        .findByIdAndUpdate(user._id, { $push: { topics_covered: topics } })
        .exec();
    }
  }

  getLastAIConversation(user: User): AIMessage {
    return _.last(
      user.history.filter(
        (h) => h.role === Role.AI && h.agent === AgentRole.CONVERSATION,
      ),
    );
  }

  removeLastInteraction(user: User) {
    return UserModel()
      .findByIdAndUpdate(user._id, { $pop: { history: 1, topics_covered: 1 } })
      .exec();
  }
}