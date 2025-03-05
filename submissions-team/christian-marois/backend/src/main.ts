import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import 'dotenv/config';

async function bootstrap() {

  const app = await NestFactory.create(AppModule, {logger: ['debug']});
  app.enableCors({
    credentials: true,
    origin: '*',
    methods: 'GET,HEAD,PUT,POST,DELETE,OPTIONS',
  });
  await app.listen(process.env.PORT ?? 3000);

}
bootstrap();

