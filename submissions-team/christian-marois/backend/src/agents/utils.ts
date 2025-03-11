export type AIMessage = {
  role: Role;
  agent: AgentRole;
  content: string;
}
export enum Role {
  SYSTEM = 'system',
  USER = 'user',
  AI = 'assistant'
}

export enum AgentRole {
  CONVERSATION =  'conversation',
  FEEDBACK =  'feedback',
  SETUP =  'setup',
  EXERCISE =  'exercise'
}


export function createSystemPrompt(content: string): AIMessage{
  return createPrompt(Role.SYSTEM, AgentRole.SETUP, content);
}
export function createUserPrompt(agent:AgentRole, content: string): AIMessage{
  return createPrompt(Role.USER, agent, content);
}
export function createAIPrompt(agent: AgentRole, content: string): AIMessage{
  return createPrompt(Role.AI, agent, content);
}

function createPrompt(role: Role,  agent: AgentRole, content: string): AIMessage{
  return {role, agent, content};
}

export function parseJSON(s: string){
  return JSON.parse(s.replaceAll('`','').replace('json', ''));
}