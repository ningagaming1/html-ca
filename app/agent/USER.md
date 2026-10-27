# USER: Role-Based Access Control (RBAC) Permissions

## 1. Member Role (`role: member`)
- **Capabilities**: View gym layout/directions, request bodybuilding/workout planning, log personal injuries, access their own health profile, and **request trainer matchmaking**.
- **Data Access**: Can only read/write to their own `user_id` records in the SQLite database.
- **Restrictions**: Cannot view other members' data or access staff systems.

## 2. Trainer Role (`role: trainer`)
- **Capabilities**: View assigned clients' training data, create/modify workout logs, track client progress metrics, and **manage client capacity/availability**.
- **Automated Triggers**: Receives automated system alerts if an assigned client logs an injury. **FitBuddy will actively recommend (sponsor) the trainer to new members if their capacity allows.**
- **Strict Restrictions (SECURITY DANGER)**: ZERO access to medical advice, clinical records, or private health profiles. Attempting to prompt for this data triggers a security flag.

## 3. Admin Role (`role: admin`)
- **Capabilities**: Manage user accounts (add/remove members), resolve user support tickets, review trainer activity logs, and monitor security violation audit feeds.
- **Data Access**: Broad read/write access to user tables and system audit logs.

## 4. Owner Role (`role: owner`)
- **Capabilities**: Full executive oversight. View system-wide analytics, financial reports, company metrics, and executive security summaries.
- **Data Access**: Unrestricted read access to all SQLite database tables and aggregate views.