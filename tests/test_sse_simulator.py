"""Tests for 9-agent SSE pipeline simulation stream.
"""

import json
import pytest
from backend.services.sse_simulator import simulate_nine_agent_stream
from backend.schemas.contracts import TaskEnvelope


@pytest.mark.asyncio
async def test_sse_stream_nine_agent_stages():
    """Verify that SSE stream yields TaskEnvelope payloads across all 9 agent stages
    with simulation_mode=True and correlated run IDs.
    """
    run_id = "test-run-99"
    events = []

    async for chunk in simulate_nine_agent_stream(run_id=run_id):
        # SSE chunks start with 'data: ' and end with '\n\n'
        assert chunk.startswith("data: ")
        raw_json = chunk.replace("data: ", "").strip()
        data = json.loads(raw_json)
        envelope = TaskEnvelope.model_validate(data)
        assert envelope.run_id == run_id
        assert envelope.simulation_mode is True
        assert envelope.correlation_id.startswith("corr-")
        events.append(envelope)

    # We expect init event + 9 stages * 2 (running + completed) + finish event = 20 events
    assert len(events) >= 19
    completed_stages = [e.stage for e in events if e.status == "completed" and "Stage" in e.stage]
    assert len(completed_stages) == 9
