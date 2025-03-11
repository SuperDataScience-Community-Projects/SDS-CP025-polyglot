import {Connection, Model, Schema} from "mongoose";
import {AIMessage} from "../agents/utils";


const userSchema = new Schema(
  {
    language: String,
    level: String,
    history: Array<AIMessage>,
    topics_covered: Array<string>,
  },
  { collection: 'users', timestamps: true }
);

let model: Model<User>;

export function createUser(conn: Connection) {
  model = conn.model<User>('users', userSchema);
}

export const getUser = (): Model<User> => {
  return model;
};

export interface User extends Document {
  _id: any;
  language: string;
  level: string;
  history: AIMessage[];
  topics_covered: string[];
}