import { useParams } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common';

export default function Sessions() {
  const { sessionId } = useParams();

  if (sessionId) {
    return <SessionDetail sessionId={sessionId} />;
  }

  return <SessionsList />;
}

function SessionsList() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Sessions</h2>
        <p className="text-muted-foreground">
          Browse all your Claude conversation sessions
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
          <CardDescription>
            Your conversation history with Claude
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent cursor-pointer"
              >
                <div className="space-y-1">
                  <p className="font-medium">Session {i}</p>
                  <p className="text-sm text-muted-foreground">
                    Project: Example Project • 45 messages • 2 hours ago
                  </p>
                </div>
                <div className="text-sm text-muted-foreground">$0.25</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function SessionDetail({ sessionId }: { sessionId: string }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          Session {sessionId}
        </h2>
        <p className="text-muted-foreground">
          Conversation details and messages
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Messages</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Conversation messages will be displayed here
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
