"""Background Worker with TelemetryFlow instrumentation example.

This example demonstrates how to instrument a background worker/job processor
with the TelemetryFlow SDK.

Usage:
    export TELEMETRYFLOW_API_KEY_ID=tfk_your_key_id
    export TELEMETRYFLOW_API_KEY_SECRET=tfs_your_key_secret
    export TELEMETRYFLOW_SERVICE_NAME=worker-example
    python main.py
"""

import random
import time
from dataclasses import dataclass
from datetime import datetime
from queue import Empty, Queue
from threading import Event, Thread

from telemetryflow import TelemetryFlowBuilder
from telemetryflow.application.commands import SpanKind
from telemetryflow.client import TelemetryFlowClient


@dataclass
class Job:
    """A job to be processed."""

    id: str
    type: str
    payload: dict
    created_at: datetime


class Worker:
    """Background worker that processes jobs with telemetry."""

    def __init__(self, client: TelemetryFlowClient, worker_id: str) -> None:
        """Initialize the worker."""
        self.client = client
        self.worker_id = worker_id
        self.job_queue: Queue[Job] = Queue()
        self.stop_event = Event()
        self.jobs_processed = 0
        self.jobs_failed = 0

    def process_job(self, job: Job) -> None:
        """Process a single job with full instrumentation."""
        # Start a span for the job
        with self.client.span(
            f"job.process.{job.type}",
            SpanKind.CONSUMER,
            {
                "job.id": job.id,
                "job.type": job.type,
                "worker.id": self.worker_id,
            },
        ) as span_id:
            start_time = time.time()

            try:
                self.client.log_info(
                    f"Processing job {job.id}",
                    {"job_type": job.type, "worker": self.worker_id},
                )

                # Increment job counter
                self.client.increment_counter(
                    "worker.jobs.started",
                    attributes={"job_type": job.type, "worker_id": self.worker_id},
                )

                # Process based on job type
                if job.type == "email":
                    self._process_email_job(job, span_id)
                elif job.type == "notification":
                    self._process_notification_job(job, span_id)
                elif job.type == "report":
                    self._process_report_job(job, span_id)
                elif job.type == "error":
                    raise ValueError("Simulated job failure")
                else:
                    self._process_generic_job(job, span_id)

                # Record success
                duration = time.time() - start_time
                self.client.increment_counter(
                    "worker.jobs.completed",
                    attributes={"job_type": job.type, "worker_id": self.worker_id},
                )
                self.client.record_histogram(
                    "worker.job.duration",
                    duration,
                    unit="s",
                    attributes={"job_type": job.type, "worker_id": self.worker_id},
                )
                self.client.add_span_event(
                    span_id, "job_completed", {"duration_ms": duration * 1000}
                )

                self.jobs_processed += 1
                self.client.log_info(
                    f"Job {job.id} completed",
                    {"duration_s": duration, "job_type": job.type},
                )

            except Exception as e:
                duration = time.time() - start_time
                self.jobs_failed += 1

                self.client.increment_counter(
                    "worker.jobs.failed",
                    attributes={"job_type": job.type, "worker_id": self.worker_id},
                )
                self.client.log_error(
                    f"Job {job.id} failed: {e}",
                    {"job_type": job.type, "duration_s": duration},
                )
                self.client.add_span_event(span_id, "job_failed", {"error": str(e)})
                raise

    def _process_email_job(self, job: Job, _parent_span_id: str) -> None:
        """Process an email job."""
        with self.client.span("email.send", SpanKind.CLIENT) as span_id:
            # Simulate email sending
            time.sleep(random.uniform(0.1, 0.3))
            self.client.add_span_event(
                span_id,
                "email_sent",
                {
                    "recipient": job.payload.get("to", "unknown"),
                    "subject": job.payload.get("subject", ""),
                },
            )

    def _process_notification_job(self, job: Job, _parent_span_id: str) -> None:
        """Process a notification job."""
        with self.client.span("notification.push", SpanKind.CLIENT) as span_id:
            # Simulate push notification
            time.sleep(random.uniform(0.05, 0.15))
            self.client.add_span_event(
                span_id,
                "notification_sent",
                {
                    "channel": job.payload.get("channel", "default"),
                    "user_id": job.payload.get("user_id", "unknown"),
                },
            )

    def _process_report_job(self, job: Job, _parent_span_id: str) -> None:
        """Process a report generation job."""
        # Database query
        with self.client.span("database.query", SpanKind.CLIENT) as span_id:
            time.sleep(random.uniform(0.2, 0.5))
            self.client.add_span_event(span_id, "query_executed", {"rows": 1000})

        # Report generation
        with self.client.span("report.generate", SpanKind.INTERNAL) as span_id:
            time.sleep(random.uniform(0.3, 0.6))
            self.client.add_span_event(
                span_id,
                "report_generated",
                {"format": job.payload.get("format", "pdf"), "pages": 15},
            )

        # Upload to storage
        with self.client.span("storage.upload", SpanKind.CLIENT) as span_id:
            time.sleep(random.uniform(0.1, 0.2))
            self.client.add_span_event(span_id, "file_uploaded", {"size_kb": 2048})

    def _process_generic_job(self, job: Job, parent_span_id: str) -> None:
        """Process a generic job."""
        time.sleep(random.uniform(0.1, 0.3))
        self.client.add_span_event(
            parent_span_id,
            "generic_processing_complete",
            {"payload_keys": list(job.payload.keys())},
        )

    def run(self) -> None:
        """Run the worker loop."""
        self.client.log_info(f"Worker {self.worker_id} started")
        self.client.record_gauge(
            "worker.active",
            1.0,
            attributes={"worker_id": self.worker_id},
        )

        while not self.stop_event.is_set():
            try:
                job = self.job_queue.get(timeout=1.0)
                try:
                    self.process_job(job)
                except Exception:
                    pass  # Error already logged
                finally:
                    self.job_queue.task_done()
            except Empty:
                # No job available, continue waiting
                pass

        self.client.record_gauge(
            "worker.active",
            0.0,
            attributes={"worker_id": self.worker_id},
        )
        self.client.log_info(
            f"Worker {self.worker_id} stopped",
            {"jobs_processed": self.jobs_processed, "jobs_failed": self.jobs_failed},
        )

    def submit_job(self, job: Job) -> None:
        """Submit a job to the queue."""
        self.job_queue.put(job)
        self.client.record_gauge(
            "worker.queue.size",
            float(self.job_queue.qsize()),
            attributes={"worker_id": self.worker_id},
        )

    def stop(self) -> None:
        """Stop the worker."""
        self.stop_event.set()


def main() -> None:
    """Main function to run the worker example."""
    # Initialize TelemetryFlow client
    client = TelemetryFlowBuilder().with_auto_configuration().build()
    client.initialize()

    print("TelemetryFlow SDK initialized!")
    print(f"Service: {client.config.service_name}")

    # Create worker
    worker = Worker(client, "worker-1")

    # Start worker thread
    worker_thread = Thread(target=worker.run, daemon=True)
    worker_thread.start()

    print("\nWorker started. Submitting sample jobs...")

    # Submit sample jobs
    sample_jobs = [
        Job(
            "job-001",
            "email",
            {"to": "user@example.com", "subject": "Welcome!"},
            datetime.now(),
        ),
        Job(
            "job-002",
            "notification",
            {"channel": "mobile", "user_id": "user-123"},
            datetime.now(),
        ),
        Job(
            "job-003",
            "report",
            {"format": "pdf", "report_type": "sales"},
            datetime.now(),
        ),
        Job(
            "job-004",
            "email",
            {"to": "admin@example.com", "subject": "Alert"},
            datetime.now(),
        ),
        Job("job-005", "generic", {"data": "test"}, datetime.now()),
        Job("job-006", "error", {}, datetime.now()),  # This will fail
        Job(
            "job-007",
            "notification",
            {"channel": "email", "user_id": "user-456"},
            datetime.now(),
        ),
    ]

    for job in sample_jobs:
        worker.submit_job(job)
        print(f"Submitted job: {job.id} ({job.type})")
        time.sleep(0.5)

    # Wait for jobs to complete
    print("\nWaiting for jobs to complete...")
    worker.job_queue.join()

    # Stop worker
    print("\nStopping worker...")
    worker.stop()
    worker_thread.join(timeout=5.0)

    # Print final status
    print("\n--- Final Status ---")
    print(f"Jobs processed: {worker.jobs_processed}")
    print(f"Jobs failed: {worker.jobs_failed}")

    status = client.get_status()
    print(f"Metrics sent: {status['metrics_sent']}")
    print(f"Logs sent: {status['logs_sent']}")
    print(f"Spans sent: {status['spans_sent']}")

    # Shutdown
    client.shutdown()
    print("\nTelemetryFlow SDK shut down!")


if __name__ == "__main__":
    main()
