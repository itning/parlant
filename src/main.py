import parlant.sdk as p
from parlant.core.loggers import LogLevel
from typing import Any


@p.tool
async def get_weather(context: p.ToolContext, city: str) -> p.ToolResult:
    return p.ToolResult(f"Sunny, 72°F in {city}")


@p.tool
async def send_otp(context: p.ToolContext, email: str) -> p.ToolResult:
    return p.ToolResult(f"验证码发送至 {email}")


@p.tool
async def verification_otp(context: p.ToolContext, code: str) -> p.ToolResult:
    return p.ToolResult(f"验证成功")


@p.tool
async def get_order_detail(context: p.ToolContext, order_id: str) -> p.ToolResult:
    return p.ToolResult(f"耐克鞋 {order_id}")


@p.tool
async def get_datetime(context: p.ToolContext) -> p.ToolResult:
    from datetime import datetime
    return p.ToolResult(datetime.now())


async def configure_hooks(hooks: p.EngineHooks) -> p.EngineHooks:
    """Configure engine hooks for the Parlant server."""

    # Hook called when the engine has encountered a runtime error
    async def on_error(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Engine error occurred: {exception}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called just before emitting an acknowledgement status event
    async def on_acknowledging(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Acknowledging message in session {context.session.id}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called right after emitting an acknowledgement status event
    async def on_acknowledged(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Acknowledged message in session {context.session.id}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called just before generating the preamble message
    async def on_generating_preamble(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Generating preamble for session {context.session.id}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called right after a preamble was generated (but not yet emitted)
    async def on_preamble_generated(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Preamble generated: {payload}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called right after a preamble message was emitted into the session
    async def on_preamble_emitted(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Preamble emitted in session {context.session.id}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called just before beginning the preparation iterations
    async def on_preparing(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Preparing for session {context.session.id}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called just before beginning a preparation iteration
    async def on_preparation_iteration_start(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Starting preparation iteration for session {context.session.id}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called right after finishing a preparation iteration
    async def on_preparation_iteration_end(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Finished preparation iteration for session {context.session.id}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called just before generating messages
    async def on_generating_messages(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Generating messages for session {context.session.id}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called right after the draft message was generated
    async def on_draft_generated(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Draft generated: {payload}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called right after a message was generated (but not yet emitted)
    async def on_message_generated(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Generated message: {payload}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called right after a single message was emitted into the session
    async def on_message_emitted(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"Message emitted: {payload}")
        return p.EngineHookResult.CALL_NEXT

    # Hook called right after all messages were emitted into the session
    async def on_messages_emitted(
            context: p.EngineContext, payload: Any, exception: Exception | None
    ) -> p.EngineHookResult:
        print(f"All messages emitted in session {context.session.id}")
        return p.EngineHookResult.CALL_NEXT

    # Register all the hooks
    hooks.on_error.append(on_error)
    hooks.on_acknowledging.append(on_acknowledging)
    hooks.on_acknowledged.append(on_acknowledged)
    hooks.on_generating_preamble.append(on_generating_preamble)
    hooks.on_preamble_generated.append(on_preamble_generated)
    hooks.on_preamble_emitted.append(on_preamble_emitted)
    hooks.on_preparing.append(on_preparing)
    hooks.on_preparation_iteration_start.append(on_preparation_iteration_start)
    hooks.on_preparation_iteration_end.append(on_preparation_iteration_end)
    hooks.on_generating_messages.append(on_generating_messages)
    hooks.on_draft_generated.append(on_draft_generated)
    hooks.on_message_generated.append(on_message_generated)
    hooks.on_message_emitted.append(on_message_emitted)
    hooks.on_messages_emitted.append(on_messages_emitted)

    return hooks


async def main():
    async with p.Server(nlp_service=p.NLPServices.qwen, log_level=LogLevel.INFO, port=7767, session_store='local',
                        variable_store='local', customer_store='local', configure_hooks=configure_hooks) as server:
        agent = await server.create_agent(
            name="客服助手",
            description="帮助客户完成售后服务"
        )

        await agent.create_variable(name="current-datetime", tool=get_datetime)

        await agent.create_guideline(
            condition="User asks about weather",
            action="Get current weather and provide a friendly response with suggestions",
            tools=[get_weather]
        )

        otp = await agent.create_journey(
            title="接收验证码",
            description="此journey引导完成发送验证码和验证验证码是否正确",
            conditions=["需要给客户发送验证码时"],
        )

        o1 = await otp.initial_state.transition_to(chat_state="询问客户的邮箱")
        o2 = await o1.target.transition_to(condition='当获得用户的邮箱', tool_state=[send_otp])
        o3 = await o2.target.transition_to(condition='成功发送验证码后', chat_state='询问用户收到的验证码')
        o4 = await o3.target.transition_to(condition='用户输入验证码后', tool_state=[verification_otp])
        await o4.target.transition_to(chat_state="告知验证结果")

        journey = await agent.create_journey(
            title="查询订单信息",
            description="此journey引导完成查询订单信息",
            conditions=["客户想要查询订单信息"],
        )
        j2 = await journey.initial_state.transition_to(condition='客户想要查询订单信息', journey=otp)
        j3 = await j2.target.transition_to(condition='当验证码验证成功', chat_state='询问用户的订单号')
        j4 = await j3.target.transition_to(condition='当获得用户的订单号', tool_state=[get_order_detail])
        j5 = await j4.target.transition_to(condition='get_order_detail tool调用成功', chat_state='告诉用户订单信息')
        await j5.target.transition_to(state=p.END_JOURNEY)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
