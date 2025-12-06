import time
import random

from celery import shared_task


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    default_retry_delay=3,
    retry_kwargs={"max_retries": 3},
)
def send_notification_task(self, transaction_id: str):
    
    print(f"Sending notification for transaction {transaction_id}...")
    
    # Simulate long request
    time.sleep(5)
    
    # Simulate random failure (for testing retry logic)
    if random.random() < 0.3:
        raise Exception("Simulated notification failure")
    
    print(f"Notification sent successfully for transaction {transaction_id}")
    return {"status": "sent", "transaction_id": transaction_id}
