# Entity-Relationship Diagram

The PreventDM data model is organized into nine entities supporting multi-tenancy across public health units, longitudinal patient risk tracking, program management, and comprehensive audit logging.

## Entity groupings

The schema is organized into three logical groupings. The first grouping handles multi-tenancy and access control through ORGANIZATIONS, USERS, and AUDIT_LOGS. The second grouping handles the clinical core through PATIENTS, RISK_ASSESSMENTS, and CLINICAL_SCORES, with each patient capable of having multiple longitudinal risk assessments. The third grouping handles program management through PROGRAMS, PROGRAM_ENROLLMENTS, and INTERVENTIONS.

## Diagram

```mermaid
erDiagram
  ORGANIZATIONS ||--o{ USERS : employs
  ORGANIZATIONS ||--o{ PATIENTS : owns
  ORGANIZATIONS ||--o{ PROGRAMS : runs
  USERS ||--o{ RISK_ASSESSMENTS : performs
  USERS ||--o{ AUDIT_LOGS : generates
  PATIENTS ||--o{ RISK_ASSESSMENTS : undergoes
  PATIENTS ||--o{ PROGRAM_ENROLLMENTS : has
  PROGRAMS ||--o{ PROGRAM_ENROLLMENTS : tracks
  PROGRAM_ENROLLMENTS ||--o{ INTERVENTIONS : includes
  RISK_ASSESSMENTS ||--o{ CLINICAL_SCORES : contains

  ORGANIZATIONS {
    uuid id PK
    string name
    string region
    timestamp created_at
  }
  USERS {
    uuid id PK
    uuid org_id FK
    string email
    string role
    string hashed_password
    timestamp created_at
  }
  PATIENTS {
    uuid id PK
    uuid org_id FK
    string external_id
    date dob
    string sex
    string ethnicity
    string postal_code
    timestamp created_at
  }
  RISK_ASSESSMENTS {
    uuid id PK
    uuid patient_id FK
    uuid performed_by FK
    timestamp assessment_date
    jsonb features
    float probability
    float confidence_lower
    float confidence_upper
    jsonb shap_values
  }
  CLINICAL_SCORES {
    uuid id PK
    uuid assessment_id FK
    string score_type
    float score_value
    string risk_category
  }
  PROGRAMS {
    uuid id PK
    uuid org_id FK
    string name
    text description
    date start_date
    date end_date
    string status
  }
  PROGRAM_ENROLLMENTS {
    uuid id PK
    uuid program_id FK
    uuid patient_id FK
    date enrolled_date
    string status
  }
  INTERVENTIONS {
    uuid id PK
    uuid enrollment_id FK
    string intervention_type
    date start_date
    date end_date
    string outcome_status
  }
  AUDIT_LOGS {
    uuid id PK
    uuid user_id FK
    uuid patient_id FK
    string action
    timestamp ts
    jsonb details
  }
```

## Design notes

The features and SHAP values in the RISK_ASSESSMENTS table are stored as jsonb columns rather than being normalized into separate tables, because the feature set is relatively wide and may evolve as the model is updated. The CLINICAL_SCORES table is normalized as a child of RISK_ASSESSMENTS rather than denormalized into the assessment itself, which allows the set of supported scores to grow over time without schema migrations. The PATIENTS table includes postal_code and ethnicity to support geographic and demographic stratification for population analytics, with the postal_code captured at the forward sortation area level rather than the full postal code to reduce reidentification risk. The AUDIT_LOGS table captures every meaningful action with a jsonb details field that holds context-specific information, supporting both PHIPA compliance and quality improvement analysis.