import {Body, Controller, Get, Post, Req, Res} from '@nestjs/common';
import { AppService } from './app.service';
import * as _ from "lodash";

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {
  }

  @Get("history")
  getHistory(@Req() req: Request & {cookies}) {
    return req.cookies["tutorSession"] || []
  }

  @Post("chat")
  async chat(
    @Req() req: Request & {cookies},
    @Res({passthrough: true}) res: Response & {cookie},
    @Body() userInput
  ) {
    let sessionMemory= req.cookies["tutorSession"] || [];

    const response = await this.appService.chat(userInput, sessionMemory);
    sessionMemory.push(..._.map(response, (d) => _.omit(d, 'voice')));
    res.cookie("tutorSession", sessionMemory.slice(0,20), {sameSite: 'Lax', httpOnly: true, secure: false,});
    return response[response.length - 1];
  }
}
