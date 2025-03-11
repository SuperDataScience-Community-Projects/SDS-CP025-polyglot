import { Body, Controller, Get, Post, Req, Res } from "@nestjs/common";
import { AppService } from "./app.service";
import * as _ from "lodash";
import { ControllerAgent } from "./agents/controller.agent";
import { AgentRole, createAIPrompt } from "./agents/utils";
import { UserService } from "./db/user.service";

@Controller()
export class AppController {
  constructor(
    private readonly appService: AppService,
    private readonly userService: UserService,
    private readonly controllerAgent: ControllerAgent,
  ) {}

  @Get("history")
  async getHistory(@Req() req: Request & { cookies }) {
    let userId = req.cookies["tutorSession"];
    if (!userId) return [];
    const response = await this.userService.getUser(userId);
    return response.history;
  }

  @Post("chat")
  async chat(
    @Req() req: Request & { cookies },
    @Res({ passthrough: true }) res: Response & { cookie },
    @Body() userInput,
  ) {
    let sessionMemory = req.cookies["tutorSession"] || [];

    const response = await this.appService.chat(userInput, sessionMemory);
    sessionMemory.push(..._.map(response, (d) => _.omit(d, "voice")));
    res.cookie("tutorSession", sessionMemory.slice(0, 20), {
      sameSite: "Lax",
      httpOnly: true,
      secure: false,
    });
    return response[response.length - 1];
  }

  @Post("tutoring")
  async advancedTutoring(
    @Req() req: Request & { cookies },
    @Res({ passthrough: true }) res: Response & { cookie },
    @Body() userInput,
  ) {
    let userId = req.cookies["tutorSession"];

    const onboarding = await this.controllerAgent.onboardUser(
      userId,
      userInput,
    );
    if (onboarding && onboarding.message !== null) {
      res.cookie("tutorSession", onboarding.userId, {
        sameSite: "Lax",
        httpOnly: true,
        secure: false,
      });
      return createAIPrompt(AgentRole.SETUP, onboarding.message);
    }
    if (onboarding) userInput.input = "";

    const response = await this.controllerAgent.processUserInput(
      userId,
      userInput.input,
    );
    return response;
  }
}
