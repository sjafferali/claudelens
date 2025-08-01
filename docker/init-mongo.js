// Switch to the claudelens database
db = db.getSiblingDB('claudelens');

// Create application user
db.createUser({
  user: 'claudelens_app',
  pwd: 'claudelens_password',
  roles: [
    {
      role: 'readWrite',
      db: 'claudelens'
    }
  ]
});

// Create collections with validation
db.createCollection('projects', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'path', 'createdAt'],
      properties: {
        name: {
          bsonType: 'string',
          description: 'Project name extracted from path'
        },
        path: {
          bsonType: 'string',
          description: 'Full path to project directory'
        },
        description: {
          bsonType: 'string',
          description: 'Optional project description'
        },
        createdAt: {
          bsonType: 'date'
        },
        updatedAt: {
          bsonType: 'date'
        }
      }
    }
  }
});

db.createCollection('sessions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['sessionId', 'projectId', 'startedAt'],
      properties: {
        sessionId: {
          bsonType: 'string',
          description: 'Unique session identifier from Claude'
        },
        projectId: {
          bsonType: 'objectId',
          description: 'Reference to project'
        },
        summary: {
          bsonType: 'string',
          description: 'AI-generated session summary'
        },
        startedAt: {
          bsonType: 'date'
        },
        endedAt: {
          bsonType: 'date'
        },
        messageCount: {
          bsonType: 'int'
        },
        totalCost: {
          bsonType: 'decimal'
        },
        metadata: {
          bsonType: 'object'
        }
      }
    }
  }
});

// Messages collection - flexible schema for Claude's varying message types
db.createCollection('messages');

// Sync state collection for CLI tool
db.createCollection('sync_state', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['projectPath', 'lastSync'],
      properties: {
        projectPath: {
          bsonType: 'string'
        },
        lastSync: {
          bsonType: 'date'
        },
        lastFile: {
          bsonType: 'string'
        },
        lastLine: {
          bsonType: 'int'
        },
        syncedHashes: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          }
        }
      }
    }
  }
});

// Create indexes
db.projects.createIndex({ path: 1 }, { unique: true });
db.projects.createIndex({ name: 'text' });

db.sessions.createIndex({ sessionId: 1 }, { unique: true });
db.sessions.createIndex({ projectId: 1 });
db.sessions.createIndex({ startedAt: -1 });
db.sessions.createIndex({ summary: 'text' });

db.messages.createIndex({ sessionId: 1, timestamp: 1 });
db.messages.createIndex({ uuid: 1 }, { unique: true });
db.messages.createIndex({ parentUuid: 1 });
db.messages.createIndex({ 'message.content': 'text', 'toolUseResult': 'text' });
db.messages.createIndex({ type: 1 });
db.messages.createIndex({ timestamp: -1 });
db.messages.createIndex({ 'message.model': 1 });
db.messages.createIndex({ costUsd: 1 });

db.sync_state.createIndex({ projectPath: 1 }, { unique: true });

print('Database initialization completed successfully');