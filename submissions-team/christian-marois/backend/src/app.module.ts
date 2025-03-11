import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import {ConversationAgent} from "./agents/conversation.agent";
import {ControllerAgent} from "./agents/controller.agent";
import {UserService} from "./db/user.service";
import {FeedbackAgent} from "./agents/feedback.agent";

@Module({
  imports: [],
  controllers: [AppController],
  providers: [AppService,
    UserService,
    FeedbackAgent,
    ControllerAgent,
    ConversationAgent],
})
export class AppModule {}
