"""Enumerations shared by every canonical model.

Lifecycle enums here MUST match the state names in contracts/state-machines/*.yaml.
tests/contract/test_state_machines.py enforces that agreement.
"""
from enum import Enum


class Purpose(str, Enum):
    DISCOVERY = "discovery"
    IMPLEMENTATION = "implementation"
    OPERATION = "operation"
    EVALUATION = "evaluation"
    TRAINING = "training"
    EXPORT = "export"
    SUPPORT = "support"


class GrantStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class VerificationLevel(str, Enum):
    """How a capability claim was established. Ordered weakest to strongest."""

    DOCUMENTED = "documented"
    LOCALLY_TESTED = "locally_tested"
    SANDBOX_TESTED = "sandbox_tested"
    ACCOUNT_VERIFIED = "account_verified"
    PRODUCTION_OBSERVED = "production_observed"


VERIFICATION_ORDER = [
    VerificationLevel.DOCUMENTED,
    VerificationLevel.LOCALLY_TESTED,
    VerificationLevel.SANDBOX_TESTED,
    VerificationLevel.ACCOUNT_VERIFIED,
    VerificationLevel.PRODUCTION_OBSERVED,
]


class CapabilityKind(str, Enum):
    SOURCE_READ = "source_read"
    SOURCE_SUBSCRIBE = "source_subscribe"
    RUNTIME_ACTION = "runtime_action"
    INTEGRATION_ADMIN = "integration_admin"
    SAAS_CONFIG = "saas_config"
    INFRA_ADMIN = "infra_admin"
    MODEL_INFERENCE = "model_inference"
    MODEL_TRAINING = "model_training"
    SOLVER = "solver"


class EffectClass(str, Enum):
    NONE = "none"
    INTERNAL = "internal"
    EXTERNAL_MESSAGE = "external_message"
    EXTERNAL_RECORD_WRITE = "external_record_write"
    EXTERNAL_PAYMENT = "external_payment"
    CONFIG_CHANGE = "config_change"
    INFRA_CHANGE = "infra_change"


class CompensationClass(str, Enum):
    NOT_NEEDED = "not_needed"
    NATIVE_UNDO = "native_undo"
    COMPENSATING_EFFECT = "compensating_effect"
    IRREVERSIBLE = "irreversible"


class RetryClass(str, Enum):
    NATURAL_IDEMPOTENT = "natural_idempotent"
    PROVIDER_KEYED = "provider_keyed"
    RECONCILABLE = "reconcilable"
    NOT_RETRYABLE_AFTER_AMBIGUITY = "not_retryable_after_ambiguity"


class ImpactClass(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


IMPACT_ORDER = [ImpactClass.LOW, ImpactClass.MEDIUM, ImpactClass.HIGH]


class StepType(str, Enum):
    """Closed set of build step types. Unknown types are rejected by the compiler (SR-040)."""

    PROBE_SOURCE = "probe_source"
    PROFILE_SOURCE = "profile_source"
    GENERATE_ADAPTER = "generate_adapter"
    TEST_ADAPTER = "test_adapter"
    CONFIGURE_INTEGRATION = "configure_integration"
    DEPLOY_COLLECTOR = "deploy_collector"
    BACKFILL = "backfill"
    RECONCILE_COLLECTOR = "reconcile_collector"
    DISCOVER_LABELS = "discover_labels"
    BUILD_DATASET = "build_dataset"
    AUDIT_LABELS = "audit_labels"
    RUN_EXPERIMENT = "run_experiment"
    SUBMIT_TRAINING = "submit_training"
    EVALUATE_CANDIDATE = "evaluate_candidate"
    COMPILE_WORKFLOW = "compile_workflow"
    GENERATE_TESTS = "generate_tests"
    REQUEST_VERIFICATION = "request_verification"
    PREVIEW_INFRA = "preview_infra"
    APPLY_INFRA = "apply_infra"
    CREATE_RELEASE = "create_release"
    AGENT_LOOP = "agent_loop"


class FactStatus(str, Enum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    STALE = "stale"
    SUPERSEDED = "superseded"


class ObligationStatus(str, Enum):
    OPEN = "open"
    PARTIALLY_SATISFIED = "partially_satisfied"
    SATISFIED = "satisfied"
    EXEMPT = "exempt"
    EXPIRED = "expired"
    REOPENED = "reopened"
    SUPERSEDED = "superseded"


class OpportunityRoute(str, Enum):
    FRICTION = "friction"
    UNMET_OBLIGATION = "unmet_obligation"
    NEW_CAPABILITY = "new_capability"


class OpportunityStatus(str, Enum):
    HYPOTHESIS = "hypothesis"
    EVIDENCED = "evidenced"
    OBJECTIVE_ACCEPTED = "objective_accepted"
    INFEASIBLE = "infeasible"
    NO_BENEFICIAL_INTERVENTION = "no_beneficial_intervention"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


class SolutionClass(str, Enum):
    REMOVE_STEP = "remove_step"
    NATIVE_CONFIGURATION = "native_configuration"
    DETERMINISTIC_RULES = "deterministic_rules"
    CLASSICAL_MODEL = "classical_model"
    GENERAL_MODEL_WORKFLOW = "general_model_workflow"
    RETRIEVAL = "retrieval"
    SPECIALIST_API = "specialist_api"
    OPTIMIZER = "optimizer"
    TRAINED_COMPONENT = "trained_component"
    DO_NOTHING = "do_nothing"


class LaborCategory(str, Enum):
    CUSTOMER_AUTHORIZATION = "customer_authorization"
    DOMAIN_CLARIFICATION = "domain_clarification"
    BUSINESS_REVIEW = "business_review"
    ENGINEERING_INTERVENTION = "engineering_intervention"
    OPERATIONAL_REPAIR = "operational_repair"
    PLATFORM_ENGINEERING = "platform_engineering"


class LabelAuthority(str, Enum):
    HISTORICAL_DECISION = "historical_decision"
    REVIEWED_APPROVAL = "reviewed_approval"
    EXPERT_ADJUDICATED = "expert_adjudicated"
    CORRECTION = "correction"
    PREFERENCE = "preference"
    BEHAVIORAL_RESPONSE = "behavioral_response"
    BUSINESS_OUTCOME = "business_outcome"
    MODEL_GENERATED = "model_generated"


class DataRole(str, Enum):
    TRAINING = "training"
    DEVELOPMENT = "development"
    CALIBRATION = "calibration"
    REGRESSION = "regression"
    PROTECTED_ACCEPTANCE = "protected_acceptance"
    PROSPECTIVE_MONITORING = "prospective_monitoring"


class CheckOutcome(str, Enum):
    PASS = "pass"
    PASS_WITH_LIMITATIONS = "pass_with_limitations"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class ApprovalKind(str, Enum):
    DATA_USE = "data_use"
    IMPLEMENT = "implement"
    RELEASE_ACTIVATION = "release_activation"
    CASE_ACTION = "case_action"
    POLICY_CHANGE = "policy_change"


class CoverageTier(str, Enum):
    EXACT_TEMPLATE = "exact_template"
    NEW_COMPOSITION = "new_composition"
    AGENT_ADAPTATION = "agent_adaptation"
    AGENT_NEW_CAPABILITY = "agent_new_capability"
    UNSUPPORTED = "unsupported"


class ProtectionClass(str, Enum):
    """Field protection applied at ingestion. See spec/privacy-and-security.md."""

    OMIT = "omit"
    TOKENIZE = "tokenize"
    PROTECTED_REFERENCE = "protected_reference"
    CLEAR = "clear"


# Lifecycle enums. Names are mirrored by contracts/state-machines/*.yaml.


class BuildState(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    RUNNING = "RUNNING"
    WAITING_AUTH = "WAITING_AUTH"
    WAITING_INPUT = "WAITING_INPUT"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepState(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    RECONCILING = "RECONCILING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class CollectorState(str, Enum):
    PLANNED = "PLANNED"
    SHADOW = "SHADOW"
    BACKFILLING = "BACKFILLING"
    RECONCILING = "RECONCILING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class DatasetState(str, Enum):
    PROPOSED = "PROPOSED"
    MATERIALIZING = "MATERIALIZING"
    QUARANTINED = "QUARANTINED"
    VERIFIED = "VERIFIED"
    SUPERSEDED = "SUPERSEDED"
    UNAVAILABLE = "UNAVAILABLE"


class TrainingState(str, Enum):
    PLANNED = "PLANNED"
    SUBMITTED = "SUBMITTED"
    SUBMISSION_UNKNOWN = "SUBMISSION_UNKNOWN"
    RUNNING = "RUNNING"
    CANDIDATE = "CANDIDATE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ReleaseState(str, Enum):
    CANDIDATE = "CANDIDATE"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    SHADOW = "SHADOW"
    CANARY = "CANARY"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ROLLED_BACK = "ROLLED_BACK"
    RETIRED = "RETIRED"


class EffectState(str, Enum):
    RESERVED = "RESERVED"
    DISPATCHING = "DISPATCHING"
    DISPATCHED = "DISPATCHED"
    UNKNOWN = "UNKNOWN"
    CONFIRMED = "CONFIRMED"
    NOT_OCCURRED = "NOT_OCCURRED"
    CONFLICT = "CONFLICT"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"
    FAILED_FINAL = "FAILED_FINAL"
    COMPENSATION_PENDING = "COMPENSATION_PENDING"
    COMPENSATED = "COMPENSATED"


class ApprovalState(str, Enum):
    REQUESTED = "REQUESTED"
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    INVALIDATED = "INVALIDATED"


class CaseState(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    WAITING_REVIEW = "WAITING_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REOPENED = "REOPENED"


class RemovalState(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    INGESTION_STOPPED = "INGESTION_STOPPED"
    IMPACT_COMPUTED = "IMPACT_COMPUTED"
    ON_HOLD = "ON_HOLD"
    ACCESS_DISABLED = "ACCESS_DISABLED"
    DERIVED_REMOVED = "DERIVED_REMOVED"
    PROVIDER_CLEANUP_PENDING = "PROVIDER_CLEANUP_PENDING"
    BACKUPS_SCHEDULED = "BACKUPS_SCHEDULED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
