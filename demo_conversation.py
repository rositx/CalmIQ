# demo_conversation.py
# Turn-by-turn simulation script to demonstrate CalmIQ middleware scoring and escalation

import asyncio
from datetime import datetime, timedelta
from guardrail.middleware import IrritationMiddleware
from guardrail.session.state import clear_all_sessions_for_testing, get_session, save_session
from guardrail.storage.store import clear_all_logs_for_testing

# Sample metadata representing a returning customer
CUSTOMER_METADATA = {
    "customer_ltv": 15000.0,          # High-LTV customer (reduces threshold by 15)
    "total_past_sessions": 2,          # Returning customer
    "recent_complaint_count": 1,       # Has past complaints (reduces threshold by 20)
    "lifetime_coupons_claimed": 0,
}

SAMPLE_CONVERSATION = [
    "Hello, I need to check the status of my refund.",
    "It has been three weeks! This delay is extremely slow.",
    "What the shit man this company is so bad no solution to my problem",
]


async def run_simulation():
    """Simulate a multi-turn chat sequence passing through the middleware."""
    clear_all_sessions_for_testing()
    clear_all_logs_for_testing()
    
    middleware = IrritationMiddleware()
    session_id = "demo_session_1"
    customer_id = "cust_99"
    
    print("=== CalmIQ AI Guardrail Middleware Simulation ===\n")
    print(f"Customer Value: ${CUSTOMER_METADATA['customer_ltv']}")
    print(f"Past Complaints: {CUSTOMER_METADATA['recent_complaint_count']}")
    print("Standard Threshold: 75 -> Adjusted Adaptive Threshold: 40\n")
    
    for turn_idx, message in enumerate(SAMPLE_CONVERSATION, 1):
        print(f"--- Turn {turn_idx} ---")
        print(f"Customer: {message}")
        
        telemetry = None
        # Simulate time elapsed before the final angry turn to satisfy hysteresis
        if turn_idx == 3:
            telemetry = {"rage_clicks": 4, "typing_speed_wpm": 160.0, "typing_pauses": 3}
            # Fetch the session and backdate the timestamp to simulate a 65-second gap
            sess = get_session(session_id)
            if sess:
                backdated_time = datetime.utcnow() - timedelta(seconds=65)
                sess.last_updated = backdated_time.isoformat()
                save_session(session_id, sess)
            
        # Process message through the interceptor
        response = await middleware.intercept_message(
            session_id=session_id,
            customer_id=customer_id,
            text=message,
            telemetry_data=telemetry,
            metadata=CUSTOMER_METADATA,
        )
        
        # Display output status and score tracking
        status = response.get("status")
        if "irritation_score" in response:
            print(f"Aggregate Irritation Score: {response.get('irritation_score'):.1f}/100")
            
        components = response.get("components")
        if components:
            s_val = components.get("sentiment_score", 0.0)
            b_val = components.get("telemetry_score")
            c_val = components.get("context_score", 0.0)
            b_str = f"{b_val:.1f}/100" if b_val is not None else "N/A (Degraded Mode)"
            print(f"  |-- [S] Sentiment Component Score: {s_val:.1f}/100")
            print(f"  |-- [B] Telemetry Component Score: {b_str}")
            print(f"  \\-- [C] Context Component Score:   {c_val:.1f}/100")
            
        if status == "normal":
            print(f"AI Bot Response: {response.get('response')}\n")
        else:
            print(f"Status: CIRCUIT BREAKER TRIGGERED ({status})")
            print(f"Primary Trigger Reason: {response.get('reason')}")
            if response.get("coupon_issued"):
                print(f"Retention Promo Code Issued: {response.get('coupon_code')}")
            print(f"Middleware Action: {response.get('message')}\n")


if __name__ == "__main__":
    asyncio.run(run_simulation())
