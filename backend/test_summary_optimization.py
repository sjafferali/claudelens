import asyncio
import sys

sys.path.insert(0, ".")


async def test_analytics():
    from app.database import get_db
    from app.schemas.analytics import TimeRange
    from app.services.analytics import AnalyticsService

    async for db in get_db():
        service = AnalyticsService(db)
        # Test the get_summary method
        try:
            summary = await service.get_summary(TimeRange.LAST_30_DAYS)
            print("✓ Summary fetched successfully!")
            print(f"  Messages: {summary.total_messages}")
            print(f"  Sessions: {summary.total_sessions}")
            print(f"  Projects: {summary.total_projects}")
            print(f"  Cost: ${summary.total_cost}")
            print(f"  Most Active Project: {summary.most_active_project}")
            print(f"  Most Used Model: {summary.most_used_model}")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback

            traceback.print_exc()
        break


if __name__ == "__main__":
    asyncio.run(test_analytics())
