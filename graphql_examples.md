# 🚀 GraphQL Examples for Anomaly Detection System

## 🌐 GraphQL Endpoint
- **URL**: `http://127.0.0.1:8000/graphql/`
- **Interactive Playground**: Visit the URL in your browser for GraphiQL interface

## 📊 **Query Examples**

### 1. Get All Log Entries
```graphql
query {
  allLogs {
    id
    timestamp
    severity
    message
  }
}
```

### 2. Get Recent Logs (Last 24 Hours)
```graphql
query {
  recentLogs(hours: 24, limit: 10) {
    id
    timestamp
    severity
    message
  }
}
```

### 3. Get Dashboard Statistics
```graphql
query {
  dashboardStats {
    anomaliesLast24h
    anomaliesLast7d
    totalLogs
    severityDistribution {
      severity
      count
    }
    lastUpdated
  }
}
```

### 4. Get All Anomaly Reports
```graphql
query {
  allAnomalies {
    id
    anomalyScore
    summary
    logEntry {
      id
      timestamp
      severity
      message
    }
  }
}
```

### 5. Search Logs by Content
```graphql
query {
  searchLogs(query: "error", limit: 5) {
    id
    timestamp
    severity
    message
  }
}
```

### 6. Get Logs by Severity
```graphql
query {
  logsBySeverity(severity: "ERROR") {
    id
    timestamp
    message
  }
}
```

### 7. Get Severity Distribution
```graphql
query {
  severityDistribution(hours: 48) {
    severity
    count
  }
}
```

### 8. Check Task Status
```graphql
query {
  taskStatus(taskId: "your-task-id-here") {
    taskId
    status
    ready
    successful
    failed
    result
    error
  }
}
```

### 9. Get Recent Anomalies
```graphql
query {
  recentAnomalies(hours: 24, limit: 5) {
    id
    anomalyScore
    summary
    logEntry {
      timestamp
      severity
      message
    }
  }
}
```

### 10. Complex Query - Dashboard with Recent Data
```graphql
query {
  dashboardStats {
    anomaliesLast24h
    anomaliesLast7d
    totalLogs
    severityDistribution {
      severity
      count
    }
  }
  recentLogs(hours: 24, limit: 5) {
    id
    timestamp
    severity
    message
  }
  recentAnomalies(hours: 24, limit: 3) {
    id
    anomalyScore
    logEntry {
      timestamp
      severity
      message
    }
  }
}
```

## 🔧 **Mutation Examples**

### 1. Create New Log Entry with Anomaly Detection
```graphql
mutation {
  createLogEntry(
    severity: "ERROR"
    message: "Database connection failed after 3 retries"
  ) {
    logEntry {
      id
      timestamp
      severity
      message
    }
    taskId
    success
  }
}
```

### 2. Trigger Pattern Analysis
```graphql
mutation {
  triggerPatternAnalysis(timeWindowHours: 24) {
    taskId
    success
    message
  }
}
```

## 🎯 **Advanced Query Examples**

### 1. Get Log with Anomaly Report (if exists)
```graphql
query {
  logById(id: 1) {
    id
    timestamp
    severity
    message
  }
  anomalyById(id: 1) {
    id
    anomalyScore
    summary
  }
}
```

### 2. Filter and Paginate Results
```graphql
query {
  recentLogs(hours: 168, limit: 20) {
    id
    timestamp
    severity
    message
  }
  severityDistribution(hours: 168) {
    severity
    count
  }
}
```

### 3. Monitor System Health
```graphql
query SystemHealth {
  dashboardStats {
    anomaliesLast24h
    totalLogs
    severityDistribution {
      severity
      count
    }
  }
  recentAnomalies(hours: 1, limit: 1) {
    id
    anomalyScore
    logEntry {
      timestamp
      severity
      message
    }
  }
}
```

## 🔍 **Testing Workflow**

### Step 1: Create Test Data
```graphql
mutation {
  createLogEntry(
    severity: "INFO"
    message: "User login successful"
  ) {
    logEntry { id }
    taskId
    success
  }
}
```

### Step 2: Create Error Log
```graphql
mutation {
  createLogEntry(
    severity: "ERROR"
    message: "Critical system failure - immediate attention required"
  ) {
    logEntry { id }
    taskId
    success
  }
}
```

### Step 3: Check Dashboard
```graphql
query {
  dashboardStats {
    anomaliesLast24h
    severityDistribution {
      severity
      count
    }
  }
}
```

### Step 4: Trigger Analysis
```graphql
mutation {
  triggerPatternAnalysis(timeWindowHours: 1) {
    taskId
    success
    message
  }
}
```

### Step 5: Monitor Task
```graphql
query {
  taskStatus(taskId: "task-id-from-step-4") {
    status
    ready
    successful
    result
  }
}
```

## 🎮 **Interactive Testing**

1. **Visit GraphiQL**: `http://127.0.0.1:8000/graphql/`
2. **Copy and paste** any of the above queries
3. **Click the play button** to execute
4. **Explore the schema** using the documentation panel
5. **Use autocomplete** with Ctrl+Space

## 🔥 **Pro Tips**

1. **Use Variables**: Define variables for dynamic queries
2. **Fragment Reuse**: Create fragments for repeated field sets
3. **Introspection**: Explore the schema with `__schema` queries
4. **Aliases**: Use aliases to fetch the same field with different parameters
5. **Nested Queries**: Combine multiple related queries in one request

Your GraphQL API is now ready for powerful, flexible querying of your anomaly detection data! 🚀
