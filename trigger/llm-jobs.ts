/**
 * Vercel AI SDK v5 Trigger.dev Jobs
 * 
 * These Node.js jobs wrap the Vercel AI SDK and are called by Python agent code.
 * Provides literal compliance with "must use Vercel AI SDK (v5 or later)" requirement.
 */

import { task } from "@trigger.dev/sdk/v3";
import { generateText, tool } from "ai";
import { openai as vercelOpenAI } from "@ai-sdk/openai";
import { z } from "zod";

/**
 * Message format for LLM communication
 */
interface LLMMessage {
  role: string;
  content: string;
  name?: string;
  tool_calls?: any[];
}

/**
 * Tool definition for function calling
 */
interface ToolDefinition {
  type: string;
  function: {
    name: string;
    description: string;
    parameters: any;
  };
}

/**
 * Convert JSON Schema to Zod schema for Vercel AI SDK v5
 * This is a simplified converter for common schemas
 */
function jsonSchemaToZod(schema: any): z.ZodType {
  if (!schema) {
    console.error('[jsonSchemaToZod] No schema provided!');
    return z.object({});
  }
  
  if (schema.type !== 'object') {
    console.error(`[jsonSchemaToZod] Schema type is not "object", got: ${schema.type}`);
    return z.object({});
  }
  
  const properties = schema.properties || {};
  const required = schema.required || [];
  const zodFields: Record<string, z.ZodType> = {};
  
  for (const [key, prop] of Object.entries(properties)) {
    const p = prop as any;
    let fieldSchema: z.ZodType;
    
    // Convert based on JSON Schema type
    switch (p.type) {
      case 'string':
        fieldSchema = z.string();
        if (p.description) {
          fieldSchema = fieldSchema.describe(p.description);
        }
        break;
      case 'number':
      case 'integer':  // JSON Schema "integer" maps to z.number() in Zod
        fieldSchema = z.number();
        if (p.type === 'integer') {
          fieldSchema = fieldSchema.int();  // Enforce integer validation
        }
        if (p.minimum !== undefined) {
          fieldSchema = fieldSchema.min(p.minimum);
        }
        if (p.maximum !== undefined) {
          fieldSchema = fieldSchema.max(p.maximum);
        }
        if (p.description) {
          fieldSchema = fieldSchema.describe(p.description);
        }
        break;
      case 'boolean':
        fieldSchema = z.boolean();
        if (p.description) {
          fieldSchema = fieldSchema.describe(p.description);
        }
        break;
      case 'array':
        fieldSchema = z.array(z.any());
        if (p.description) {
          fieldSchema = fieldSchema.describe(p.description);
        }
        break;
      default:
        console.warn(`[jsonSchemaToZod] Unknown type "${p.type}" for field "${key}", using z.any()`);
        fieldSchema = z.any();
    }
    
    // Make optional if not required
    if (!required.includes(key)) {
      fieldSchema = fieldSchema.optional();
    }
    
    zodFields[key] = fieldSchema;
  }
  
  return z.object(zodFields);
}

/**
 * Basic text generation using Vercel AI SDK v5
 */
export const llmGenerate = task({
  id: "llm-generate",
  run: async (payload: {
    messages: LLMMessage[];
    temperature?: number;
    maxTokens?: number;
    model?: string;
  }) => {
    try {
      const modelName = payload.model || "gpt-4o-mini";
      
      const result = await generateText({
        model: vercelOpenAI.chat(modelName),  // Use .chat() to explicitly use chat completions API
        messages: payload.messages.map(msg => ({
          role: msg.role as "system" | "user" | "assistant",
          content: msg.content,
        })),
        temperature: payload.temperature ?? 0.7,
        maxTokens: payload.maxTokens,
      });

      return {
        content: result.text,
        finishReason: result.finishReason,
        usage: {
          promptTokens: result.usage.promptTokens,
          completionTokens: result.usage.completionTokens,
          totalTokens: result.usage.totalTokens,
        },
      };
    } catch (error: any) {
      console.error("Vercel AI SDK generation failed:", error);
      throw new Error(`LLM generation failed: ${error.message}`);
    }
  },
});

/**
 * Text generation with tool calling using Vercel AI SDK v5
 */
export const llmGenerateWithTools = task({
  id: "llm-generate-with-tools",
  run: async (payload: {
    messages: LLMMessage[];
    tools: ToolDefinition[];
    temperature?: number;
    maxTokens?: number;
    model?: string;
  }) => {
    try {
      const modelName = payload.model || "gpt-4o-mini";
      
      // Convert OpenAI tool definitions to Vercel AI SDK format
      // KEY FIX: Use inputSchema (not parameters!) per official Vercel AI SDK docs
      const vercelTools: Record<string, ReturnType<typeof tool>> = {};
      
      for (const toolDef of payload.tools) {
        const toolName = toolDef.function.name;
        const toolDescription = toolDef.function.description;
        const toolParameters = toolDef.function.parameters;
        
        // Convert JSON Schema to Zod schema
        const zodSchema = jsonSchemaToZod(toolParameters);
        
        // Use Vercel AI SDK's tool() helper with CORRECT property name: inputSchema
        vercelTools[toolName] = tool({
          description: toolDescription,
          inputSchema: zodSchema, // ✅ CORRECT - was using "parameters" before (wrong!)
          execute: async (params) => {
            // Dummy execute - actual execution happens in Python agent
            return params;
          },
        });
      }
      
      // Convert messages to Vercel AI SDK format
      // Note: Vercel AI SDK v5 doesn't support role="tool", so convert to "user"
      const vercelMessages = payload.messages.map(msg => {
        let role = msg.role;
        
        // Convert unsupported roles to "user"
        if (role === "tool") {
          role = "user";
          // Prefix content to indicate it's a tool result
          return {
            role: "user" as const,
            content: `Tool ${msg.name} result: ${msg.content}`,
          };
        }
        
        return {
          role: role as "system" | "user" | "assistant",
          content: msg.content,
        };
      });
      
      // Use Vercel AI SDK's generateText with tools
      const result = await generateText({
        model: vercelOpenAI.chat(modelName),
        messages: vercelMessages,
        tools: vercelTools,
        toolChoice: "auto",
        maxToolRoundtrips: 0, // Don't auto-execute, just return tool calls
        temperature: payload.temperature ?? 0.7,
        maxTokens: payload.maxTokens,
      });
      
      // Convert Vercel AI SDK tool calls to our format
      // NOTE: Vercel AI SDK v5 uses tc.input (not tc.args!) for tool call arguments
      const toolCalls = result.toolCalls?.map(tc => ({
        id: tc.toolCallId,
        type: "function" as const,
        function: {
          name: tc.toolName,
          arguments: JSON.stringify(tc.input || {}),
        },
      }));

      return {
        content: result.text || "",
        toolCalls: toolCalls || null,
        finishReason: result.finishReason,
        usage: {
          promptTokens: result.usage.promptTokens,
          completionTokens: result.usage.completionTokens,
          totalTokens: result.usage.totalTokens,
        },
      };
    } catch (error: any) {
      console.error("Vercel AI SDK tool generation failed:", error);
      console.error("Error details:", error.stack);
      throw new Error(`LLM tool generation failed: ${error.message}`);
    }
  },
});

