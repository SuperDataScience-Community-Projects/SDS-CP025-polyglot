import {Connection, createConnection, Model, Query} from "mongoose";
import {createUser, getUser, User} from "./user.schema";
import * as dotenv from "dotenv";

dotenv.config();

var __setOptions = Query.prototype.setOptions;

Query.prototype.setOptions = function (options: any) {
  __setOptions.apply(this, arguments);
  if (!this.mongooseOptions.lean) {
    this.mongooseOptions({ lean: true });
  }
  return this;
};


let db: Connection;

export function connectToDB() {
  const dbhost = process.env.MONGO_HOST;
  const u = process.env.MONGO_USER;
  const p = process.env.MONGO_PASS;
  const url = `mongodb://${u}:${p}@${dbhost}`;

  const opts = {
    ssl: false,
  };
  opts.ssl = process.env.MONGO_SSL === 'true';
  db = createConnection(url, opts);
  db.useDb(process.env.MONGO_DB ?? 'Tutor');

  db.startSession();
  db.on('open', () =>  {
    console.log('Mongo DB connected');
  });
  db.on('error', (e) => {
    console.error('MongoDB connection error:', e);
  });
  createUser(db)


}

export const UserModel = (): Model<User> =>
  getUser();
