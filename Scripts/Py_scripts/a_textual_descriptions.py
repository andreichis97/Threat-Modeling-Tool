text_description = """
Organization: ShopNova — a fictional mid-size e-commerce company selling consumer electronics and accessories. ShopNova operates a web storefront, mobile app, and integrates with third-party logistics, payment, and analytics providers.
________________________________________
1. BPMN Diagram: Order Processing & Fulfillment
Diagram Name: BPMN_OrderProcessing
This process describes how a customer places an order on the ShopNova platform and how the order is fulfilled through internal systems and external logistics.
Process Elements
Start Event: Customer initiates a new order session on the ShopNova web storefront or mobile app.
Task: Browse Product Catalog The customer searches and browses products using the catalog interface. Product details, availability, and pricing are retrieved from the product database.
Task: Add Items to Shopping Cart The customer selects one or more products and adds them to a persistent shopping cart. The cart state is maintained server-side and associated with the customer's session or account.
Task: Initiate Checkout The customer proceeds to checkout, providing or confirming shipping address, selecting a shipping method, and entering billing information. The system validates address format and shipping eligibility.
Sub-Process: Process Payment (Decomposed in DFD — see Section 2) The payment sub-process handles validation of payment credentials, fraud screening, transaction execution via an external payment gateway, and receipt generation. This is the sub-process that is decomposed into a Data Flow Diagram.
Exclusive Gateway: Payment Authorized?
•	Yes proceed to Confirm Order.
•	No proceed to Notify Payment Failure.
Task: Notify Payment Failure The system notifies the customer that payment could not be authorized and presents options to retry with different payment details or cancel the order. The event is logged for analytics.
End Event Failure: The process ends after failed payment notification.
Task: Confirm Order The system generates an order confirmation number and persists the order record. A confirmation email and push notification are sent to the customer with order details and estimated delivery date.
Task: Allocate Inventory The inventory management system reserves stock for the confirmed order. If stock is insufficient at the primary warehouse, the system checks secondary warehouses and triggers a backorder workflow if needed.
Task: Package Order Warehouse staff receive a pick list, collect items, perform quality checks, and package the order. A shipping label is generated via the logistics integration.
Task: Ship Order The packaged order is handed off to the shipping carrier. The system records the tracking number and updates the order status to "Shipped."
Task: Update Delivery Status The system periodically polls the carrier's tracking API to update delivery status. The customer receives notifications at key milestones (out for delivery, delivered). Upon confirmed delivery, the order status is set to "Delivered."
End Event Successful: Order successfully delivered to the customer.
________________________________________
2. DFD Diagram: Process Payment
Diagram Name: DFD_ProcessPayment
This Data Flow Diagram decomposes the "Process Payment" sub-process from the BPMN diagram above. It shows how payment data flows between external actors, internal processes, and data stores during a payment transaction.
________________________________________
External Entities
EE1: Customer Description: The end-user who initiates the payment by submitting payment credentials (credit card, digital wallet) through the ShopNova checkout interface. Trust Boundary: Resides outside the Internal Network Boundary (in the External Users Zone). Threats:
•	T1 — Customer Identity Spoofing Mitigations:
•	M1 — Multi-Factor Authentication
•	M4 — Input Validation and Integrity Checks
EE2: Payment Gateway Provider (StripeConnect) Description: The external payment processor that authorizes and settles credit card and digital wallet transactions on behalf of ShopNova. Trust Boundary: Resides outside the PCI Compliance Zone (in the External Services Zone). Threats:
•	T2 — Gateway Communication Tampering
•	T6 — Transaction Repudiation Mitigations:
•	M2 — TLS 1.3 with Certificate Pinning
•	M6 — Comprehensive Transaction Logging
EE3: Fraud Detection Service (FraudShield) Description: A third-party fraud scoring service that evaluates transactions against behavioral analytics and known fraud patterns. Trust Boundary: Resides outside the Internal Network Boundary (in the External Services Zone). Threats:
•	T3 — Fraud Service Response Spoofing
•	T5 — Fraud Screening Denial of Service Mitigations:
•	M3 — Mutual TLS Authentication
________________________________________
Processes
P1: Validate Payment Details Description: Receives raw payment input from the customer, validates card number format (Luhn check), expiration date, and CVV presence. Enriches the request with the customer's profile data from the Customer Database. Trust Boundary: Resides inside the Internal Network Boundary. Threats:
•	T4 — Payment Data Tampering in Transit
•	T1 — Customer Identity Spoofing Mitigations:
•	M4 — Input Validation and Integrity Checks
•	M1 — Multi-Factor Authentication
P2: Screen for Fraud Description: Sends the validated payment request to the external Fraud Detection Service and cross-references the transaction against internal fraud rules. Returns an approve/reject/review decision. Trust Boundary: Resides inside the Internal Network Boundary. Threats:
•	T5 — Fraud Screening Denial of Service
•	T3 — Fraud Service Response Spoofing
•	T6 — Transaction Repudiation Mitigations:
•	M5 — Rate Limiting and Circuit Breaker
•	M3 — Mutual TLS Authentication
P3: Execute Payment Transaction Description: Sends the authorized payment request to the Payment Gateway Provider, receives the transaction result (approved/declined), and persists the transaction record. Trust Boundary: Resides inside the PCI Compliance Zone. Threats:
•	T6 — Transaction Repudiation
•	T9 — Payment Record Tampering Mitigations:
•	M6 — Comprehensive Transaction Logging
•	M9 — Database Integrity Controls and Write-Audit Logging
•	M11 — Immutable Append-Only Log Storage
P4: Generate Payment Receipt Description: Creates a payment receipt with masked card details and transaction summary, stores it in the Audit Log, and delivers it to the customer. Trust Boundary: Resides inside the Internal Network Boundary. Threats:
•	T7 — Sensitive Data Leakage in Receipts
•	T11 — Audit Trail Tampering Mitigations:
•	M7 — PII Data Masking in Output
•	M11 — Immutable Append-Only Log Storage
________________________________________
Data Stores
DS1: Customer Database Description: Central relational database storing customer profiles, addresses, payment method tokens, and order history. Shared across multiple ShopNova subsystems. Trust Boundary: Resides inside the Internal Network Boundary. Threats:
•	T8 — Unauthorized Access to Customer PII
•	T1 — Customer Identity Spoofing Mitigations:
•	M8 — Encryption at Rest with RBAC
•	M10 — Privileged Access Management
•	M1 — Multi-Factor Authentication
DS2: Payment Records Description: PCI-compliant data store holding transaction records, authorization codes, settlement statuses, and tokenized card references. Trust Boundary: Resides inside the PCI Compliance Zone. Threats:
•	T9 — Payment Record Tampering
•	T8 — Unauthorized Access to Customer PII Mitigations:
•	M9 — Database Integrity Controls and Write-Audit Logging
•	M11 — Immutable Append-Only Log Storage
DS3: Fraud Rules Repository Description: Stores configurable fraud detection rules, velocity thresholds, blacklisted card BINs, and geolocation risk scores used by the internal fraud screening logic. Trust Boundary: Resides inside the Internal Network Boundary. Threats:
•	T10 — Unauthorized Fraud Rule Modification Mitigations:
•	M10 — Privileged Access Management
DS4: Audit Log Description: Append-only log capturing all payment-related events, state transitions, and administrative actions for compliance and forensic purposes. Shared across multiple ShopNova subsystems. Trust Boundary: Resides inside the Internal Network Boundary. Threats:
•	T11 — Audit Trail Tampering
•	T6 — Transaction Repudiation Mitigations:
•	M11 — Immutable Append-Only Log Storage
•	M6 — Comprehensive Transaction Logging
________________________________________
Trust Boundaries
TB1: External Users Zone Description: Represents the untrusted network zone where end-user devices (browsers, mobile apps) operate. All traffic from this zone is considered untrusted and must be authenticated and encrypted before entering the internal network.
TB2: Internal Network Boundary Description: The corporate network perimeter that encloses ShopNova's application servers, internal services, and non-PCI data stores. Protected by firewalls and network segmentation from external zones.
TB3: PCI Compliance Zone Description: A highly restricted network segment that processes and stores cardholder data in compliance with PCI-DSS. Access is limited to authorized services and all data at rest and in transit is encrypted. Subject to quarterly vulnerability scans and annual audits.
TB4: External Services Zone Description: Represents the zone where third-party service providers (payment gateway, fraud detection) operate. Communication with this zone requires encrypted channels and mutual authentication where applicable.
________________________________________
Data Flows
DF1: Payment Details Submission Name: Payment Details Submission Description: The customer submits payment credentials (card number, expiry, CVV or digital wallet token) to the Validate Payment Details process. Protocol: HTTPS Crosses Trust Boundaries: Yes — from External Users Zone (TB1) into Internal Network Boundary (TB2). Threats:
•	T4 — Payment Data Tampering in Transit
•	T1 — Customer Identity Spoofing Mitigations:
•	M4 — Input Validation and Integrity Checks
•	M1 — Multi-Factor Authentication
DF2: Customer Profile Lookup Name: Customer Profile Lookup Description: The Validate Payment Details process queries the Customer Database to retrieve the customer's stored profile and payment token history. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Network Boundary (TB2).
DF3: Validated Payment Request Name: Validated Payment Request Description: The validated and enriched payment request is forwarded from the Validate Payment Details process to the Screen for Fraud process. Protocol: HTTPS Crosses Trust Boundaries: No — both reside within the Internal Network Boundary (TB2).
DF4: Fraud Check Request Name: Fraud Check Request Description: The Screen for Fraud process sends transaction data to the external Fraud Detection Service for risk scoring. Protocol: HTTPS Crosses Trust Boundaries: Yes — Internal Network Boundary (TB2), PCI Compliance Zone (TB3) and External Services Zone (TB4)z. Threats:
•	T3 — Fraud Service Response Spoofing Mitigations:
•	M3 — Mutual TLS Authentication
DF5: Fraud Scoring Response Name: Fraud Scoring Response Description: The Fraud Detection Service returns a risk score and decision (approve/decline/manual review) to the Screen for Fraud process. Protocol: HTTPS Crosses Trust Boundaries: Yes — External Services Zone (TB4), PCI Compliance Zone (TB3) and Internal Network Boundary (TB2). Threats:
•	T3 — Fraud Service Response Spoofing
•	T5 — Fraud Screening Denial of Service Mitigations:
•	M3 — Mutual TLS Authentication
•	M5 — Rate Limiting and Circuit Breaker
DF6: Fraud Rules Query Name: Fraud Rules Query Description: The Screen for Fraud process queries the Fraud Rules Repository for applicable velocity checks, BIN blacklists, and risk thresholds. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Network Boundary (TB2).
DF7: Approved Payment Request Name: Approved Payment Request Description: The fraud-cleared payment request is forwarded from the Screen for Fraud process to the Execute Payment Transaction process. Protocol: HTTPS Crosses Trust Boundaries: Yes — Internal Network Boundary (TB2) and PCI Compliance Zone (TB3). Threats:
•	T4 — Payment Data Tampering in Transit Mitigations:
•	M2 — TLS 1.3 with Certificate Pinning
DF8: Transaction Authorization Request Name: Transaction Authorization Request Description: The Execute Payment Transaction process sends the payment authorization request to the Payment Gateway Provider. Protocol: HTTPS Crosses Trust Boundaries: Yes — PCI Compliance Zone (TB3) and External Services Zone (TB4). Threats:
•	T2 — Gateway Communication Tampering Mitigations:
•	M2 — TLS 1.3 with Certificate Pinning
•	M6 — Comprehensive Transaction Logging
DF9: Transaction Authorization Response Name: Transaction Authorization Response Description: The Payment Gateway Provider returns the authorization result (approved, declined, or error) to the Execute Payment Transaction process. Protocol: HTTPS Crosses Trust Boundaries: Yes — External Services Zone (TB4) and PCI Compliance Zone (TB3). Threats:
•	T2 — Gateway Communication Tampering Mitigations:
•	M2 — TLS 1.3 with Certificate Pinning
DF10: Payment Record Storage Name: Payment Record Storage Description: The Execute Payment Transaction process writes the completed transaction record (authorization code, amount, status, timestamp) to the Payment Records data store. Protocol: TLS Crosses Trust Boundaries: No — both reside within the PCI Compliance Zone (TB3).
DF11: Receipt Generation Data Name: Receipt Generation Data Description: The Execute Payment Transaction process sends the transaction summary to the Generate Payment Receipt process for receipt creation. Protocol: HTTPS Crosses Trust Boundaries: Yes — PCI Compliance Zone (TB3) and Internal Network Boundary (TB2). Threats:
•	T7 — Sensitive Data Leakage in Receipts Mitigations:
•	M7 — PII Data Masking in Output
DF12: Receipt Delivery Name: Receipt Delivery Description: The Generate Payment Receipt process sends the formatted receipt (with masked card details) to the customer via email and in-app notification. Protocol: HTTPS Crosses Trust Boundaries: Yes — Internal Network Boundary (TB2) and External Users Zone (TB1). Threats:
•	T7 — Sensitive Data Leakage in Receipts Mitigations:
•	M7 — PII Data Masking in Output
DF13: Audit Log Entry Name: Audit Log Entry Description: The Generate Payment Receipt process writes a log entry capturing the receipt generation event, including a hash of the receipt content, to the Audit Log. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Network Boundary (TB2).
Data Flows Links
DF1: Payment Details Submission — From EE1 (Customer) to P1 (Validate Payment Details)
DF2: Customer Profile Lookup — From P1 (Validate Payment Details) to DS1 (Customer Database)
DF3: Validated Payment Request — From P1 (Validate Payment Details) to P2 (Screen for Fraud)
DF4: Fraud Check Request — From P2 (Screen for Fraud) to EE3 (Fraud Detection Service / FraudShield)
DF5: Fraud Scoring Response — From EE3 (Fraud Detection Service / FraudShield) to P2 (Screen for Fraud)
DF6: Fraud Rules Query — From P2 (Screen for Fraud) to DS3 (Fraud Rules Repository)
DF7: Approved Payment Request — From P2 (Screen for Fraud) to P3 (Execute Payment Transaction)
DF8: Transaction Authorization Request — From P3 (Execute Payment Transaction) to EE2 (Payment Gateway Provider / StripeConnect)
DF9: Transaction Authorization Response — From EE2 (Payment Gateway Provider / StripeConnect) to P3 (Execute Payment Transaction)
DF10: Payment Record Storage — From P3 (Execute Payment Transaction) to DS2 (Payment Records)
DF11: Receipt Generation Data — From P3 (Execute Payment Transaction) to P4 (Generate Payment Receipt)
DF12: Receipt Delivery — From P4 (Generate Payment Receipt) to EE1 (Customer)
DF13: Audit Log Entry — From P4 (Generate Payment Receipt) to DS4 (Audit Log)
________________________________________
3. Threat Modeling Diagram: Process Payment Threats
Diagram Name: TM_ProcessPayment
This threat modeling diagram captures the threats and mitigations associated with the DFD_ProcessPayment diagram. Each threat is linked to at least one DFD element and belongs to a threat category from the Threat/Mitigation Categorization diagram (see Section 4).
Threats
T1: Customer Identity Spoofing Threat Category: Spoofing Risk Level: Critical Likelihood: High Description: An attacker impersonates a legitimate customer by using stolen credentials or session tokens to initiate fraudulent payment transactions. This is exacerbated by weak or single-factor authentication on the checkout flow.
T2: Gateway Communication Tampering Threat Category: Tampering Risk Level: High Likelihood: Medium Description: An attacker performs a man-in-the-middle attack on the communication channel between the Execute Payment Transaction process and the Payment Gateway Provider, attempting to modify transaction amounts or redirect funds.
T3: Fraud Service Response Spoofing Threat Category: Spoofing Risk Level: High Likelihood: Low Description: An attacker intercepts or spoofs responses from the external Fraud Detection Service, injecting fabricated low-risk scores to bypass fraud screening for malicious transactions.
T4: Payment Data Tampering in Transit Threat Category: Tampering Risk Level: High Likelihood: Medium Description: Payment details (card number, CVV, amount) are modified during transmission from the customer's browser to the Validate Payment Details process, potentially through browser-based malware or compromised network infrastructure.
T5: Fraud Screening Denial of Service Threat Category: Denial of Service Risk Level: Medium Likelihood: Medium Description: An attacker floods the fraud screening process or the external Fraud Detection Service with a high volume of requests, degrading or disabling fraud checks and allowing fraudulent transactions to pass through unscreened.
T6: Transaction Repudiation Threat Category: Repudiation Risk Level: Medium Likelihood: High Description: A customer or internal actor disputes that a payment transaction occurred or claims the transaction amount was different, and insufficient logging makes it impossible to produce non-repudiable evidence of the original transaction.
T7: Sensitive Data Leakage in Receipts Threat Category: Information Disclosure Risk Level: Medium Likelihood: Medium Description: Payment receipts inadvertently include unmasked card numbers, CVVs, or other sensitive payment details, exposing cardholder data to unauthorized parties through email interception or insecure storage.
T8: Unauthorized Access to Customer PII Threat Category: Information Disclosure Risk Level: Critical Likelihood: Medium Description: An attacker gains unauthorized read access to the Customer Database, exfiltrating personally identifiable information including names, addresses, email addresses, and tokenized payment references.
T9: Payment Record Tampering Threat Category: Tampering Risk Level: Critical Likelihood: Low Description: An attacker or malicious insider modifies payment transaction records in the Payment Records data store, altering amounts, statuses, or timestamps to conceal fraud or embezzlement.
T10: Unauthorized Fraud Rule Modification Threat Category: Elevation of Privilege Risk Level: High Likelihood: Low Description: An attacker escalates privileges to gain write access to the Fraud Rules Repository, weakening or disabling fraud detection thresholds to allow fraudulent transactions to pass undetected.
T11: Audit Trail Tampering Threat Category: Repudiation Risk Level: High Likelihood: Low Description: An attacker or malicious insider modifies or deletes entries in the Audit Log to cover traces of unauthorized actions, undermining the integrity of the forensic record and enabling repudiation of malicious transactions.
Mitigations
M1: Multi-Factor Authentication Mitigation Category: Authentication & Identity Control Type: Preventive Implementation Status: Implemented Cost Type: Medium Cost Value: 15000 Description: Enforces multi-factor authentication (password + OTP or biometric) for all customer payment transactions, reducing the risk of identity spoofing through stolen credentials.
M2: TLS 1.3 with Certificate Pinning Mitigation Category: Network Security Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 5000 Description: All communication with the Payment Gateway Provider uses TLS 1.3 with certificate pinning to prevent man-in-the-middle attacks and ensure data integrity in transit.
M3: Mutual TLS Authentication Mitigation Category: Authentication & Identity Control Type: Preventive Implementation Status: Implemented Cost Type: Medium Cost Value: 12000 Description: Establishes mutual TLS authentication between the internal fraud screening process and the external Fraud Detection Service, ensuring both parties verify each other's identity before exchanging data.
M4: Input Validation and Integrity Checks Mitigation Category: Input Validation Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 3000 Description: Applies strict server-side input validation (Luhn check, format validation, range checks) and computes integrity hashes on payment data to detect any tampering between the client and the validation process.
M5: Rate Limiting and Circuit Breaker Mitigation Category: Availability & Resilience Control Type: Preventive Implementation Status: Partially Implemented Cost Type: Medium Cost Value: 10000 Description: Implements per-client rate limiting on the fraud screening endpoint and a circuit breaker pattern that fails-closed (blocks transactions) when the fraud service is degraded, preventing both abuse and unscreened pass-through.
M6: Comprehensive Transaction Logging Mitigation Category: Logging & Monitoring Control Type: Detective Implementation Status: Implemented Cost Type: Low Cost Value: 4000 Description: Records all transaction events with cryptographically signed timestamps, including request payloads, authorization codes, and response statuses, providing non-repudiable evidence for dispute resolution.
M7: PII Data Masking in Output Mitigation Category: Data Protection Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 2000 Description: All outbound receipts and notifications apply PII masking rules — card numbers are truncated to last four digits, CVVs are never included, and sensitive fields are redacted before leaving the internal network.
M8: Encryption at Rest with RBAC Mitigation Category: Data Protection Control Type: Preventive Implementation Status: Implemented Cost Type: High Cost Value: 25000 Description: The Customer Database encrypts all PII fields using AES-256 at rest and enforces role-based access control, limiting data access to authorized service accounts with least-privilege permissions.
M9: Database Integrity Controls and Write-Audit Logging Mitigation Category: Data Protection Control Type: Detective Implementation Status: Implemented Cost Type: High Cost Value: 18000 Description: Payment Records enforce database-level integrity constraints (check constraints, triggers) and maintain a separate write-audit log that records every modification with the authenticated principal, old value, and new value.
M10: Privileged Access Management Mitigation Category: Access Control Control Type: Preventive Implementation Status: Partially Implemented Cost Type: High Cost Value: 30000 Description: Write access to the Fraud Rules Repository is restricted through a privileged access management solution requiring approval workflows, session recording, and just-in-time credential provisioning for authorized administrators only.
M11: Immutable Append-Only Log Storage Mitigation Category: Logging & Monitoring Control Type: Preventive Implementation Status: Implemented Cost Type: Medium Cost Value: 14000 Description: The Audit Log is stored on a WORM (Write Once Read Many) storage backend with cryptographic chaining, ensuring that no entry can be modified or deleted after creation, even by privileged administrators.
Threat-to-Mitigation Mapping — Case 1 (Process Payment)
T1: Customer Identity Spoofing → M1 (Multi-Factor Authentication), M4 (Input Validation and Integrity Checks)
T2: Gateway Communication Tampering → M2 (TLS 1.3 with Certificate Pinning)
T3: Fraud Service Response Spoofing → M3 (Mutual TLS Authentication)
T4: Payment Data Tampering in Transit → M2 (TLS 1.3 with Certificate Pinning), M4 (Input Validation and Integrity Checks)
T5: Fraud Screening Denial of Service → M5 (Rate Limiting and Circuit Breaker)
T6: Transaction Repudiation → M6 (Comprehensive Transaction Logging), M11 (Immutable Append-Only Log Storage)
T7: Sensitive Data Leakage in Receipts → M7 (PII Data Masking in Output), M8 (Encryption at Rest with RBAC)
T8: Unauthorized Access to Customer PII → M8 (Encryption at Rest with RBAC), M10 (Privileged Access Management)
T9: Payment Record Tampering → M9 (Database Integrity Controls and Write-Audit Logging), M11 (Immutable Append-Only Log Storage)
T10: Unauthorized Fraud Rule Modification → M10 (Privileged Access Management)
T11: Audit Trail Tampering → M11 (Immutable Append-Only Log Storage), M6 (Comprehensive Transaction Logging)

________________________________________
4. Threat/Mitigation Categorization Diagram
Diagram Name: CAT_ThreatMitigationCategorization
This diagram defines the threat categories and mitigation categories used across all five threat modeling diagrams. Below are the categories introduced in Case 1 (additional categories may be introduced in subsequent cases).
Threat Categories
Spoofing Description: Threats involving an attacker impersonating another user, system, or service to gain unauthorized access or perform unauthorized actions. Relates to violations of authentication mechanisms.
Tampering Description: Threats involving unauthorized modification of data in transit or at rest, including alteration of messages, records, or configuration to subvert system integrity.
Repudiation Description: Threats where an actor denies having performed an action and the system lacks sufficient evidence (logs, signatures, timestamps) to prove otherwise.
Information Disclosure Description: Threats involving the exposure of sensitive or confidential information to unauthorized parties, whether through direct access, side channels, or inadequate output sanitization.
Denial of Service Description: Threats aimed at degrading or disabling system availability by overwhelming resources, exploiting resource exhaustion vulnerabilities, or disrupting dependent services.
Elevation of Privilege Description: Threats where an attacker gains access rights beyond what was originally granted, allowing them to perform administrative or restricted operations without proper authorization.
Mitigation Categories
Authentication & Identity Control Description: Mitigations that verify the identity of users, services, or systems before granting access. Includes multi-factor authentication, mutual TLS, certificate validation, and identity federation.
Network Security Description: Mitigations that protect data in transit and enforce secure communication channels. Includes TLS enforcement, certificate pinning, network segmentation, and firewall rules.
Input Validation Description: Mitigations that validate, sanitize, and verify the integrity of all incoming data before processing. Includes format checks, schema validation, and integrity hashing.
Availability & Resilience Description: Mitigations that maintain system availability under adverse conditions. Includes rate limiting, circuit breakers, failover mechanisms, and capacity planning.
Logging & Monitoring Description: Mitigations that provide audit trails, event logging, and real-time monitoring for detection, forensics, and non-repudiation. Includes immutable logs, SIEM integration, and cryptographic timestamping.
Data Protection Description: Mitigations that protect data confidentiality and integrity at rest and in output. Includes encryption, data masking, tokenization, and role-based access control on data stores.
Access Control Description: Mitigations that enforce authorization policies and least-privilege principles. Includes privileged access management, approval workflows, and just-in-time access provisioning.

Case 2/5 — Customer Registration & Account Management
Organization: ShopNova — a fictional mid-size e-commerce company selling consumer electronics and accessories. ShopNova operates a web storefront, mobile app, and integrates with third-party logistics, payment, and analytics providers.
________________________________________
1. BPMN Diagram: Customer Registration & Account Management
Diagram Name: BPMN_CustomerAccountManagement
This process describes how a new customer registers on the ShopNova platform and how existing customers manage their account profiles, preferences, and security settings.
Process Elements
Start Event: A visitor accesses the ShopNova registration page or an existing customer navigates to their account settings.
Exclusive Gateway: New or Existing Customer?
•	New → proceed to Register Account.
•	Existing → proceed to Authenticate Customer.
Task: Register Account The visitor fills in a registration form providing their name, email address, password, and optionally a phone number. The system validates the email format and enforces password complexity requirements.
Task: Send Verification Email The system dispatches a verification email containing a single-use, time-limited token to the provided email address via the external email delivery service. The token expires after 24 hours.
Task: Verify Email Address The visitor clicks the verification link. The system validates the token, marks the email as verified, and activates the account. If the token has expired, the system prompts the visitor to request a new verification email.
Task: Authenticate Customer An existing customer provides login credentials (email and password). The system validates the credentials against stored hashes and, if multi-factor authentication is enabled, prompts for a second factor.
Sub-Process: Manage Customer Profile (Decomposed in DFD — see Section 2) The profile management sub-process handles viewing, editing, and validating customer profile data — including personal details, shipping addresses, communication preferences, and security settings such as password changes and MFA enrollment. This is the sub-process that is decomposed into a Data Flow Diagram.
Exclusive Gateway: Profile Changes Saved?
•	Yes → proceed to Send Profile Update Confirmation.
•	No → proceed to Display Validation Errors.
Task: Display Validation Errors The system presents field-level validation errors to the customer, indicating which profile fields failed validation and why (e.g., invalid phone format, duplicate email address).
End Event Validation Failure: The process ends after displaying validation errors; the customer may retry.
Task: Send Profile Update Confirmation The system sends a confirmation notification (email and/or push notification) summarizing the profile changes made, including a timestamp and the option to revert changes within 48 hours if the changes were not authorized.
Task: Log Account Activity All account-related actions (registration, login, profile changes, password resets, MFA changes) are written to the centralized audit log for compliance and security monitoring.
End Event Successful: Account registration or profile update completed successfully.
________________________________________
2. DFD Diagram: Manage Customer Profile
Diagram Name: DFD_ManageCustomerProfile
This Data Flow Diagram decomposes the "Manage Customer Profile" sub-process from the BPMN diagram above. It shows how profile data flows between external actors, internal processes, and data stores when a customer views or modifies their account profile.
External Entities
EE1: Customer Description: The authenticated end-user who views or modifies their profile through the ShopNova web storefront or mobile app. This is the same Customer entity used in Case 1 (DFD_ProcessPayment). Trust Boundary: Resides outside the Internal Application Zone (in the External Users Zone). Threats:
•	T12 — Account Takeover via Credential Stuffing
•	T19 — Session Fixation Attack Mitigations:
•	M12 — Credential Stuffing Detection and Blocking
•	M19 — Secure Session Management
EE4: Email Delivery Service (SendGrid) Description: A third-party transactional email service that dispatches account verification emails, profile change confirmations, and security alert notifications on behalf of ShopNova. Trust Boundary: Resides outside the Internal Application Zone (in the External Users Zone). Threats:
•	T20 — Email Notification Content Injection Mitigations:
•	M20 — Email Content Sanitization and Templating
Processes
P5: Authenticate and Authorize User Description: Validates the customer's session token or credentials, checks the account status (active, locked, suspended), and determines the customer's authorization level before allowing profile access. Trust Boundary: Resides inside the Internal Application Zone. Threats:
•	T12 — Account Takeover via Credential Stuffing
•	T17 — Account Lockout Denial of Service
•	T19 — Session Fixation Attack Mitigations:
•	M12 — Credential Stuffing Detection and Blocking
•	M17 — Progressive Account Lockout Policy
•	M19 — Secure Session Management
P6: Retrieve Customer Profile Description: Fetches the customer's current profile data from the Customer Database and formats it for display, applying field-level access control to restrict which fields the customer can view (e.g., masked payment tokens are shown but not full card numbers). Trust Boundary: Resides inside the Internal Application Zone. Threats:
•	T15 — Customer PII Exposure via API Response Mitigations:
•	M15 — API Response Field Filtering
•	M7 — PII Data Masking in Output
P7: Validate and Apply Profile Changes Description: Receives the customer's profile modification request, validates all changed fields (email format, phone format, address completeness), checks for conflicts (duplicate email), applies the changes to the Customer Database, and triggers a confirmation notification. Trust Boundary: Resides inside the Internal Application Zone. Threats:
•	T13 — Profile Data Tampering
•	T18 — Privilege Escalation via Profile Role Manipulation
•	T14 — Unauthorized Profile Change Repudiation Mitigations:
•	M4 — Input Validation and Integrity Checks
•	M18 — Role Assignment Validation
•	M13 — Profile Change Verification Workflow
P8: Dispatch Notification Description: Composes and sends profile-related notifications (change confirmations, security alerts, revert links) to the customer via the external Email Delivery Service and in-app push notifications. Trust Boundary: Resides inside the Internal Application Zone. Threats:
•	T20 — Email Notification Content Injection
•	T15 — Customer PII Exposure via API Response Mitigations:
•	M20 — Email Content Sanitization and Templating
Data Stores
DS1: Customer Database Description: Central relational database storing customer profiles, addresses, payment method tokens, and order history. Shared across multiple ShopNova subsystems. This is the same data store used in Case 1 (DFD_ProcessPayment). Trust Boundary: Resides inside the Internal Application Zone. Threats:
•	T16 — Account Enumeration Attack
•	T13 — Profile Data Tampering
•	T8 — Unauthorized Access to Customer PII Mitigations:
•	M8 — Encryption at Rest with RBAC
•	M16 — Account Enumeration Prevention
DS4: Audit Log Description: Append-only log capturing all account-related events, profile modifications, authentication attempts, and administrative actions for compliance and forensic purposes. Shared across multiple ShopNova subsystems. This is the same data store used in Case 1 (DFD_ProcessPayment). Trust Boundary: Resides inside the Internal Application Zone. Threats:
•	T21 — Audit Log Bypass on Profile Changes Mitigations:
•	M11 — Immutable Append-Only Log Storage
•	M14 — Detailed Profile Change Audit Trail
•	M6 — Comprehensive Transaction Logging
DS5: Session Store Description: An in-memory data store (Redis-backed) holding active session tokens, their associated user identifiers, device fingerprints, and expiration timestamps. Trust Boundary: Resides inside the Internal Application Zone. Threats:
•	T19 — Session Fixation Attack
•	T12 — Account Takeover via Credential Stuffing Mitigations:
•	M19 — Secure Session Management
Trust Boundaries
TB1: External Users Zone Description: Represents the untrusted network zone where end-user devices (browsers, mobile apps) and third-party email delivery services operate. All traffic from this zone is considered untrusted and must be authenticated and encrypted before entering the internal application zone.
TB5: Internal Application Zone Description: The secured internal zone enclosing ShopNova's application servers, internal APIs, data stores, and session management infrastructure. Protected by a web application firewall, API gateway, and network-level access controls.
Data Flows
DF14: Profile Access Request Name: Profile Access Request Description: The customer submits a request to view or edit their profile, including their session token for authentication. Protocol: HTTPS Crosses Trust Boundaries: Yes — External Users Zone (TB1) and Internal Application Zone (TB5).  From: EE1 (Customer) → P5 (Authenticate and Authorize User) Threats:
•	T12 — Account Takeover via Credential Stuffing
•	T19 — Session Fixation Attack Mitigations:
•	M12 — Credential Stuffing Detection and Blocking
•	M19 — Secure Session Management
DF15: Session Validation Query Name: Session Validation Query Description: The Authenticate and Authorize User process queries the Session Store to verify the customer's session token validity, expiration, and device binding. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Application Zone (TB5). From: P5 (Authenticate and Authorize User) → DS5 (Session Store)
DF16: Profile Data Request Name: Profile Data Request Description: The Retrieve Customer Profile process queries the Customer Database for the customer's full profile record. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Application Zone (TB5). From: P6 (Retrieve Customer Profile) → DS1 (Customer Database)
DF17: Profile Display Response Name: Profile Display Response Description: The Retrieve Customer Profile process sends the formatted and field-filtered profile data back to the customer's browser or app. Protocol: HTTPS Crosses Trust Boundaries: Yes — Internal Application Zone (TB5) and External Users Zone (TB1). From: P6 (Retrieve Customer Profile) → EE1 (Customer) Threats:
•	T15 — Customer PII Exposure via API Response Mitigations:
•	M15 — API Response Field Filtering
•	M7 — PII Data Masking in Output
DF18: Profile Modification Submission Name: Profile Modification Submission Description: The customer submits modified profile fields (name, email, phone, address, password, MFA settings) to the Validate and Apply Profile Changes process. Protocol: HTTPS Crosses Trust Boundaries: Yes — Internal Application Zone (TB5) and External Users Zone (TB1). From: EE1 (Customer) → P7 (Validate and Apply Profile Changes) Threats:
•	T13 — Profile Data Tampering
•	T18 — Privilege Escalation via Profile Role Manipulation Mitigations:
•	M4 — Input Validation and Integrity Checks
•	M18 — Role Assignment Validation
DF19: Profile Update Write Name: Profile Update Write Description: The Validate and Apply Profile Changes process writes the validated profile changes to the Customer Database. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Application Zone (TB5). From: P7 (Validate and Apply Profile Changes) → DS1 (Customer Database) Threats:
•	T13 — Profile Data Tampering Mitigations:
•	M8 — Encryption at Rest with RBAC
DF20: Profile Change Audit Entry Name: Profile Change Audit Entry Description: The Validate and Apply Profile Changes process writes a detailed audit record capturing which fields were changed, old values (hashed for sensitive fields), new values, timestamp, and the authenticated principal. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Application Zone (TB5). From: P7 (Validate and Apply Profile Changes) → DS4 (Audit Log) Threats:
•	T14 — Unauthorized Profile Change Repudiation Mitigations:
•	M14 — Detailed Profile Change Audit Trail
DF21: Notification Trigger Name: Notification Trigger Description: The Validate and Apply Profile Changes process sends a notification request to the Dispatch Notification process, containing the change summary and recipient details. Protocol: HTTPS Crosses Trust Boundaries: No — both reside within the Internal Application Zone (TB5). From: P7 (Validate and Apply Profile Changes) → P8 (Dispatch Notification)
DF22: Email Dispatch Request Name: Email Dispatch Request Description: The Dispatch Notification process sends the composed email (subject, body, recipient) to the external Email Delivery Service for delivery. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Internal Application Zone (TB5) to External Users Zone (TB1). From: P8 (Dispatch Notification) → EE4 (Email Delivery Service / SendGrid) Threats:
•	T20 — Email Notification Content Injection Mitigations:
•	M20 — Email Content Sanitization and Templating
DF23: Authentication Audit Entry Name: Authentication Audit Entry Description: The Authenticate and Authorize User process writes an audit record for every authentication attempt (successful or failed), capturing IP address, device fingerprint, timestamp, and outcome. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Application Zone (TB5). From: P5 (Authenticate and Authorize User) → DS4 (Audit Log) Threats:
•	T21 — Audit Log Bypass on Profile Changes Mitigations:
•	M11 — Immutable Append-Only Log Storage
DF24: Authorized Session Handoff Name: Authorized Session Handoff Description: After successful authentication, the Authenticate and Authorize User process passes the authenticated customer context to the Retrieve Customer Profile process. Protocol: HTTPS Crosses Trust Boundaries: No — both reside within the Internal Application Zone (TB5). From: P5 (Authenticate and Authorize User) → P6 (Retrieve Customer Profile)
________________________________________
3. Threat Modeling Diagram: Manage Customer Profile Threats
Diagram Name: TM_ManageCustomerProfile
This threat modeling diagram captures the threats and mitigations associated with the DFD_ManageCustomerProfile diagram. Each threat is linked to at least one DFD element and belongs to a threat category from the Threat/Mitigation Categorization diagram (see Section 4).
Threats
T12: Account Takeover via Credential Stuffing Threat Category: Spoofing Risk Level: Critical Likelihood: High Description: An attacker uses automated tools to test large volumes of stolen username/password pairs (from breaches of other services) against the ShopNova login endpoint, exploiting password reuse to gain unauthorized access to customer accounts.
T13: Profile Data Tampering Threat Category: Tampering Risk Level: High Likelihood: Medium Description: An attacker modifies profile data in transit or manipulates API parameters to alter fields beyond the customer's authorized scope, such as changing the associated email to hijack the account or modifying shipping addresses for order redirection.
T14: Unauthorized Profile Change Repudiation Threat Category: Repudiation Risk Level: Medium Likelihood: Medium Description: A customer or compromised account disputes that profile changes were made, and the system lacks sufficiently detailed audit records to prove who initiated the change, from which device, and at what time.
T15: Customer PII Exposure via API Response Threat Category: Information Disclosure Risk Level: High Likelihood: Medium Description: The profile retrieval API returns more data than the client needs, inadvertently exposing sensitive fields such as full date of birth, internal account identifiers, or hashed passwords in the JSON response body.
T16: Account Enumeration Attack Threat Category: Information Disclosure Risk Level: Medium Likelihood: High Description: An attacker exploits differences in the system's response to valid vs. invalid email addresses during registration or password reset, allowing them to enumerate which email addresses have active ShopNova accounts.
T17: Account Lockout Denial of Service Threat Category: Denial of Service Risk Level: Medium Likelihood: Medium Description: An attacker deliberately triggers repeated failed login attempts against targeted customer accounts, causing the accounts to become locked and denying legitimate customers access to their profiles and purchasing ability.
T18: Privilege Escalation via Profile Role Manipulation Threat Category: Elevation of Privilege Risk Level: Critical Likelihood: Low Description: An attacker manipulates the profile update request to inject or modify role-related fields (e.g., is_admin, account_type), exploiting insufficient server-side validation to escalate their privileges from a regular customer to an administrative role.
T19: Session Fixation Attack Threat Category: Spoofing Risk Level: High Likelihood: Low Description: An attacker sets a known session identifier on the victim's browser before authentication, then uses that same session identifier after the victim logs in to hijack the authenticated session and access the victim's profile.
T20: Email Notification Content Injection Threat Category: Tampering Risk Level: Medium Likelihood: Low Description: An attacker crafts profile field values (e.g., name field) containing malicious content (HTML, scripts, phishing links) that are rendered unsanitized in the profile change confirmation email, potentially phishing other recipients or injecting tracking content.
T21: Audit Log Bypass on Profile Changes Threat Category: Repudiation Risk Level: High Likelihood: Low Description: A flaw in the profile management application logic allows certain profile changes to bypass the audit logging mechanism, leaving no forensic record of the modification and enabling actors to make undetectable changes to customer data.
Mitigations
M12: Credential Stuffing Detection and Blocking Mitigation Category: Authentication & Identity Control Type: Preventive Implementation Status: Implemented Cost Type: Medium Cost Value: 20000 Description: Deploys behavioral analysis and IP reputation scoring on the login endpoint to detect credential stuffing patterns (high-velocity login attempts from distributed IPs with high failure rates), automatically blocking or CAPTCHA-challenging suspicious sources.
M13: Profile Change Verification Workflow Mitigation Category: Authentication & Identity Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 5000 Description: Critical profile changes (email address, password, MFA settings) require re-authentication and trigger a confirmation email to the original email address with a time-limited revert link, ensuring the account owner is aware of and consents to the change.
M14: Detailed Profile Change Audit Trail Mitigation Category: Logging & Monitoring Control Type: Detective Implementation Status: Implemented Cost Type: Low Cost Value: 4000 Description: Every profile modification is logged with the full change context: authenticated user, session ID, source IP, device fingerprint, fields changed, old values (hashed for sensitive fields), new values, and cryptographically signed timestamp.
M15: API Response Field Filtering Mitigation Category: Data Protection Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 3500 Description: The profile API enforces a strict allowlist of fields returned per endpoint, stripping internal identifiers, hashed passwords, and any fields not required by the consuming client, reducing the attack surface for information disclosure.
M16: Account Enumeration Prevention Mitigation Category: Authentication & Identity Control Type: Preventive Implementation Status: Partially Implemented Cost Type: Low Cost Value: 2500 Description: The registration and password reset endpoints return identical response codes, messages, and timing regardless of whether the email address exists in the system, preventing attackers from distinguishing between valid and invalid accounts.
M17: Progressive Account Lockout Policy Mitigation Category: Availability & Resilience Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 3000 Description: Implements exponentially increasing lockout durations (30s, 2m, 15m, 1h) after consecutive failed login attempts, combined with CAPTCHA challenges, limiting the impact of brute-force attacks while allowing legitimate users to regain access relatively quickly.
M18: Role Assignment Validation Mitigation Category: Access Control Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 2000 Description: The profile update API enforces a server-side allowlist of mutable fields per role. Role-related fields, internal flags, and account-type attributes are explicitly excluded from customer-facing update endpoints and any unexpected fields in the request payload are rejected.
M19: Secure Session Management Mitigation Category: Authentication & Identity Control Type: Preventive Implementation Status: Implemented Cost Type: Medium Cost Value: 8000 Description: Sessions are regenerated upon successful authentication with cryptographically random identifiers, bound to TLS session parameters and device fingerprint, marked as HttpOnly and Secure, and expire after 30 minutes of inactivity.
M20: Email Content Sanitization and Templating Mitigation Category: Input Validation Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 2500 Description: All user-supplied data inserted into email notifications is HTML-encoded and sanitized against injection attacks. Emails are generated from pre-approved templates with parameterized placeholders, preventing arbitrary content injection.
Threat-to-Mitigation Mapping — Case 2 (Manage Customer Profile)
T12: Account Takeover via Credential Stuffing → M12 (Credential Stuffing Detection and Blocking), M19 (Secure Session Management), M13 (Profile Change Verification Workflow) 
T13: Profile Data Tampering → M4 (Input Validation and Integrity Checks), M8 (Encryption at Rest with RBAC) 
T14: Unauthorized Profile Change Repudiation → M14 (Detailed Profile Change Audit Trail), M6 (Comprehensive Transaction Logging) 
T15: Customer PII Exposure via API Response → M15 (API Response Field Filtering), M7 (PII Data Masking in Output) 
T16: Account Enumeration Attack → M16 (Account Enumeration Prevention) 
T17: Account Lockout Denial of Service → M17 (Progressive Account Lockout Policy), M12 (Credential Stuffing Detection and Blocking) 
T18: Privilege Escalation via Profile Role Manipulation → M18 (Role Assignment Validation), M4 (Input Validation and Integrity Checks) 
T19: Session Fixation Attack → M19 (Secure Session Management) 
T20: Email Notification Content Injection → M20 (Email Content Sanitization and Templating) 
T21: Audit Log Bypass on Profile Changes → M11 (Immutable Append-Only Log Storage), M14 (Detailed Profile Change Audit Trail)

Case 3/5 — Product Review Submission & Moderation
Organization: ShopNova — a fictional mid-size e-commerce company selling consumer electronics and accessories. ShopNova operates a web storefront, mobile app, and integrates with third-party logistics, payment, and analytics providers.
________________________________________
1. BPMN Diagram: Product Review & Rating Management
Diagram Name: BPMN_ProductReviewManagement
This process describes how customers submit product reviews on the ShopNova platform and how those reviews are moderated, approved, and published to the product catalog.
Process Elements
Start Event: A customer navigates to a previously purchased product's page and selects "Write a Review."
Task: Verify Purchase Eligibility The system checks whether the customer has a confirmed and delivered order containing the product. Only customers with a verified purchase are permitted to submit a review.
Exclusive Gateway: Purchase Verified?
•	Yes → proceed to Submit Review.
•	No → proceed to Display Eligibility Rejection.
Task: Display Eligibility Rejection The system informs the customer that they cannot review this product because no qualifying purchase was found. The customer is offered the option to browse other products they have purchased.
End Event Rejection: The process ends after displaying the eligibility rejection.
Sub-Process: Submit and Moderate Review (Decomposed in DFD — see Section 2) The review sub-process handles receiving the review text and rating, validating content against submission rules, screening the content through an external moderation service, and either approving or rejecting the review. This is the sub-process that is decomposed into a Data Flow Diagram.
Exclusive Gateway: Review Approved?
•	Yes → proceed to Publish Review.
•	No → proceed to Notify Review Rejection.
Task: Notify Review Rejection The system notifies the customer that their review did not pass content moderation, providing a general reason (policy violation, inappropriate language) without revealing specific moderation logic. The customer may revise and resubmit.
End Event Rejection: The process ends after notifying the customer of the rejection.
Task: Publish Review The approved review and rating are published to the product page and the product's aggregate rating is recalculated. The review appears publicly with the reviewer's display name (not their real name or email).
Task: Send Review Confirmation The system sends a confirmation notification to the customer that their review has been published, including a link to view it on the product page.
Task: Log Review Activity All review-related actions (submission, moderation decision, publication, rejection) are written to the centralized audit log for compliance, analytics, and dispute resolution.
End Event Successful: Review published and confirmation sent.
________________________________________
2. DFD Diagram: Submit and Moderate Review
Diagram Name: DFD_SubmitModerateReview
This Data Flow Diagram decomposes the "Submit and Moderate Review" sub-process from the BPMN diagram above. It shows how review data flows between external actors, internal processes, and data stores during review submission, moderation, and publication.
External Entities
EE1: Customer Description: The authenticated end-user who submits a product review containing a star rating (1–5), review title, review body text, and optionally uploaded photos. This is the same Customer entity used in Cases 1 and 2. Trust Boundary: Resides outside the Internal Content Management Zone. Threats:
•	T22 — Fake Review Identity Spoofing
•	T26 — Review Submission Flooding Mitigations:
•	M21 — Verified Purchase Requirement
•	M23 — Review Submission Rate Limiting
EE5: Content Moderation Service (ModerateAI) Description: A third-party AI-powered content moderation service that screens review text and images for policy violations, hate speech, spam, and competitor promotional content. Trust Boundary: Resides outside the Internal Content Management Zone. Threats:
•	T27 — Moderation Bypass via Content Obfuscation Mitigations:
•	M27 — Automated Content Policy Enforcement
Processes
P9: Receive and Validate Review Description: Receives the customer's review submission, validates the star rating range (1–5), enforces minimum and maximum text lengths, checks for duplicate submissions on the same product, and verifies the customer's purchase eligibility against the Product Catalog. Trust Boundary: Resides inside the Internal Content Management Zone. Threats:
•	T22 — Fake Review Identity Spoofing
•	T26 — Review Submission Flooding
•	T24 — Review Authorship Denial Mitigations:
•	M21 — Verified Purchase Requirement
•	M23 — Review Submission Rate Limiting
•	M4 — Input Validation and Integrity Checks
P10: Screen Review Content Description: Sends the validated review text and any attached images to the external Content Moderation Service for policy screening, and applies internal keyword filters. Returns an approve, reject, or manual-review decision. Trust Boundary: Resides inside the Internal Content Management Zone. Threats:
•	T27 — Moderation Bypass via Content Obfuscation
•	T29 — Moderation Decision Repudiation Mitigations:
•	M22 — Review Content Filtering and Sanitization
•	M25 — Moderation Action Logging
P11: Publish Approved Review Description: Writes the approved review to the Product Reviews Database, recalculates the product's aggregate rating in the Product Catalog, anonymizes the reviewer's identity for public display, and sends a publication notification to the customer. Trust Boundary: Resides inside the Internal Content Management Zone. Threats:
•	T28 — Review Score Tampering in Database
•	T25 — Reviewer Purchase History Exposure Mitigations:
•	M24 — Review Integrity Checksums
•	M26 — Reviewer Anonymization in Public Display
Data Stores
DS6: Product Reviews Database Description: Stores all submitted reviews including text, rating, moderation status, timestamps, reviewer identifier, and associated product reference. Supports full-text search and aggregate rating computation. Trust Boundary: Resides inside the Internal Content Management Zone. Threats:
•	T23 — Review Content Manipulation After Submission
•	T28 — Review Score Tampering in Database Mitigations:
•	M24 — Review Integrity Checksums
•	M11 — Immutable Append-Only Log Storage
DS7: Product Catalog Description: Stores product metadata including name, description, pricing, stock status, and aggregate review rating. The review publication process updates the aggregate rating field when new reviews are approved. Trust Boundary: Resides inside the Internal Content Management Zone. Threats:
•	T28 — Review Score Tampering in Database Mitigations:
•	M4 — Input Validation and Integrity Checks
DS4: Audit Log Description: Append-only log capturing all review-related events — submissions, moderation decisions, publications, and rejections — for compliance and dispute resolution. Shared across multiple ShopNova subsystems. This is the same data store used in Cases 1 and 2. Trust Boundary: Resides inside the Internal Content Management Zone. Threats:
•	T29 — Moderation Decision Repudiation
•	T24 — Review Authorship Denial Mitigations:
•	M11 — Immutable Append-Only Log Storage
•	M6 — Comprehensive Transaction Logging
•	M25 — Moderation Action Logging
Trust Boundaries
TB6: Internal Content Management Zone Description: The secured internal zone enclosing ShopNova's review processing services, content moderation pipeline, product catalog services, and associated data stores. Protected by the API gateway with authentication enforcement, request validation, and egress filtering for external service calls.
Data Flows
DF25: Review Submission Name: Review Submission Description: The customer submits a product review containing a star rating, title, body text, and optional images to the Receive and Validate Review process. Protocol: HTTPS Crosses Trust Boundaries: Yes — from outside into Internal Content Management Zone (TB6). From: EE1 (Customer) → P9 (Receive and Validate Review) Threats:
•	T22 — Fake Review Identity Spoofing
•	T26 — Review Submission Flooding Mitigations:
•	M21 — Verified Purchase Requirement
•	M23 — Review Submission Rate Limiting
DF26: Purchase Verification Query Name: Purchase Verification Query Description: The Receive and Validate Review process queries the Product Catalog to verify that the customer has a confirmed purchase of the product being reviewed. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Content Management Zone (TB6). From: P9 (Receive and Validate Review) → DS7 (Product Catalog)
DF27: Validated Review Handoff Name: Validated Review Handoff Description: The validated review data (text, rating, reviewer ID, product ID) is passed from the Receive and Validate Review process to the Screen Review Content process for moderation. Protocol: HTTPS Crosses Trust Boundaries: No — both reside within the Internal Content Management Zone (TB6). From: P9 (Receive and Validate Review) → P10 (Screen Review Content)
DF28: Content Moderation Request Name: Content Moderation Request Description: The Screen Review Content process sends the review text and attached images to the external Content Moderation Service for automated policy screening. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Internal Content Management Zone (TB6) to outside. From: P10 (Screen Review Content) → EE5 (Content Moderation Service / ModerateAI) Threats:
•	T27 — Moderation Bypass via Content Obfuscation Mitigations:
•	M22 — Review Content Filtering and Sanitization
DF29: Moderation Result Name: Moderation Result Description: The Content Moderation Service returns a moderation verdict (approve, reject, manual review) with confidence scores and flagged content categories to the Screen Review Content process. Protocol: HTTPS Crosses Trust Boundaries: Yes — from outside into Internal Content Management Zone (TB6). From: EE5 (Content Moderation Service / ModerateAI) → P10 (Screen Review Content) Threats:
•	T23 — Review Content Manipulation After Submission Mitigations:
•	M22 — Review Content Filtering and Sanitization
•	M25 — Moderation Action Logging
DF30: Approved Review for Publication Name: Approved Review for Publication Description: The moderation-cleared review data is forwarded from the Screen Review Content process to the Publish Approved Review process. Protocol: HTTPS Crosses Trust Boundaries: No — both reside within the Internal Content Management Zone (TB6). From: P10 (Screen Review Content) → P11 (Publish Approved Review)
DF31: Published Review Storage Name: Published Review Storage Description: The Publish Approved Review process writes the approved review record (text, rating, anonymized reviewer display name, product ID, timestamp) to the Product Reviews Database. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Content Management Zone (TB6). From: P11 (Publish Approved Review) → DS6 (Product Reviews Database) Threats:
•	T28 — Review Score Tampering in Database Mitigations:
•	M24 — Review Integrity Checksums
DF32: Product Rating Update Name: Product Rating Update Description: The Publish Approved Review process sends the new rating value to update the product's aggregate rating in the Product Catalog. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Content Management Zone (TB6). From: P11 (Publish Approved Review) → DS7 (Product Catalog)
DF33: Review Submission Audit Entry Name: Review Submission Audit Entry Description: The Receive and Validate Review process writes an audit record capturing the review submission event, including reviewer identity, product reference, timestamp, and validation outcome. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Content Management Zone (TB6). From: P9 (Receive and Validate Review) → DS4 (Audit Log) Threats:
•	T24 — Review Authorship Denial Mitigations:
•	M6 — Comprehensive Transaction Logging
DF34: Review Publication Notification Name: Review Publication Notification Description: The Publish Approved Review process sends a confirmation notification to the customer that their review has been published, including a direct link to the review on the product page. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Internal Content Management Zone (TB6) to outside. From: P11 (Publish Approved Review) → EE1 (Customer) Threats:
•	T25 — Reviewer Purchase History Exposure Mitigations:
•	M26 — Reviewer Anonymization in Public Display
•	M7 — PII Data Masking in Output
________________________________________
3. Threat Modeling Diagram: Submit and Moderate Review Threats
Diagram Name: TM_SubmitModerateReview
This threat modeling diagram captures the threats and mitigations associated with the DFD_SubmitModerateReview diagram. Each threat is linked to at least one DFD element and belongs to a threat category from the Threat/Mitigation Categorization diagram (see Section 4).
Threats
T22: Fake Review Identity Spoofing Threat Category: Spoofing Risk Level: Critical Likelihood: Medium Description: An attacker submits fraudulent reviews by impersonating other customers, using compromised accounts or exploiting weaknesses in the purchase verification logic to post reviews for products they never purchased, manipulating product reputation.
T23: Review Content Manipulation After Submission Threat Category: Tampering Risk Level: Medium Likelihood: Low Description: An attacker or insider modifies review text or rating values after the review has passed moderation and been stored, either by directly tampering with database records or by intercepting and altering the moderation response in transit.
T24: Review Authorship Denial Threat Category: Repudiation Risk Level: Low Likelihood: Medium Description: A customer denies having submitted a review (e.g., after posting defamatory content), and the system lacks sufficient audit evidence tying the review submission to the authenticated customer's session and identity.
T25: Reviewer Purchase History Exposure Threat Category: Information Disclosure Risk Level: Medium Likelihood: Medium Description: The review publication or notification flow inadvertently reveals the reviewer's purchase history, real name, or account details through the public-facing review display or the confirmation notification, enabling profiling or social engineering.
T26: Review Submission Flooding Threat Category: Denial of Service Risk Level: Medium Likelihood: High Description: An attacker uses automated scripts to submit a massive volume of review requests, overwhelming the review processing pipeline and external moderation service, degrading review functionality for legitimate customers.
T27: Moderation Bypass via Content Obfuscation Threat Category: Elevation of Privilege Risk Level: High Likelihood: Low Description: An attacker crafts review content using homoglyph substitution, invisible Unicode characters, or image-embedded text to bypass the automated content moderation filters, publishing policy-violating content (spam, hate speech, competitor promotions) that the moderation service fails to detect.
T28: Review Score Tampering in Database Threat Category: Tampering Risk Level: High Likelihood: Low Description: An attacker or malicious insider directly modifies rating values in the Product Reviews Database or the aggregate rating in the Product Catalog, artificially inflating or deflating product scores to manipulate customer purchasing decisions.
T29: Moderation Decision Repudiation Threat Category: Repudiation Risk Level: Medium Likelihood: Low Description: A moderation decision (approve or reject) cannot be traced back to the specific moderation logic, external service response, or manual reviewer that made the determination, making it impossible to audit why a particular review was published or suppressed.
Mitigations
M21: Verified Purchase Requirement Mitigation Category: Authentication & Identity Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 3500 Description: The review submission endpoint enforces server-side validation that the authenticated customer has at least one delivered order containing the target product, preventing reviews from non-purchasers and making spoofed reviews significantly harder.
M22: Review Content Filtering and Sanitization Mitigation Category: Input Validation Control Type: Preventive Implementation Status: Implemented Cost Type: Medium Cost Value: 12000 Description: All review text is normalized (Unicode canonicalization, homoglyph resolution), stripped of hidden characters, and passed through both the external moderation service and an internal keyword filter before approval. Images are scanned for embedded text and steganographic content.
M23: Review Submission Rate Limiting Mitigation Category: Availability & Resilience Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 2500 Description: Enforces per-customer and per-IP rate limits on review submissions (maximum 5 reviews per customer per day, 20 per IP per hour), with CAPTCHA challenges triggered at 50% of the threshold, preventing automated flooding.
M24: Review Integrity Checksums Mitigation Category: Data Protection Control Type: Detective Implementation Status: Implemented Cost Type: Low Cost Value: 3000 Description: Each published review record includes a cryptographic hash (SHA-256) of the review text, rating, and reviewer ID, computed at publication time and verified on retrieval, enabling detection of any post-publication tampering with review content or scores.
M25: Moderation Action Logging Mitigation Category: Logging & Monitoring Control Type: Detective Implementation Status: Implemented Cost Type: Low Cost Value: 4000 Description: Every moderation decision is logged with the full context: review ID, external moderation service response (including confidence scores and flagged categories), internal filter results, final decision, and timestamp, enabling full auditability of moderation outcomes.
M26: Reviewer Anonymization in Public Display Mitigation Category: Data Protection Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 2000 Description: Published reviews display only the reviewer's chosen display name (defaulting to first name + last initial). Real name, email, account ID, order details, and purchase history are never exposed in the public review display or API responses.
M27: Automated Content Policy Enforcement Mitigation Category: Access Control Control Type: Preventive Implementation Status: Partially Implemented Cost Type: Medium Cost Value: 15000 Description: A layered moderation pipeline applies multiple independent detection methods (NLP classification, pattern matching, image analysis) with a fail-closed policy — reviews that cannot be confidently classified are routed to manual review rather than auto-approved.
Threat-to-Mitigation Mapping — Case 3 (Submit and Moderate Review)
T22: Fake Review Identity Spoofing → M21 (Verified Purchase Requirement), M4 (Input Validation and Integrity Checks) 
T23: Review Content Manipulation After Submission → M24 (Review Integrity Checksums), M22 (Review Content Filtering and Sanitization) 
T24: Review Authorship Denial → M6 (Comprehensive Transaction Logging), M25 (Moderation Action Logging) 
T25: Reviewer Purchase History Exposure → M26 (Reviewer Anonymization in Public Display), M7 (PII Data Masking in Output) 
T26: Review Submission Flooding → M23 (Review Submission Rate Limiting) 
T27: Moderation Bypass via Content Obfuscation → M27 (Automated Content Policy Enforcement), M22 (Review Content Filtering and Sanitization) 
T28: Review Score Tampering in Database → M24 (Review Integrity Checksums), M11 (Immutable Append-Only Log Storage) 
T29: Moderation Decision Repudiation → M25 (Moderation Action Logging), M11 (Immutable Append-Only Log Storage)

Case 4/5 — Return & Refund Processing
Organization: ShopNova — a fictional mid-size e-commerce company selling consumer electronics and accessories. ShopNova operates a web storefront, mobile app, and integrates with third-party logistics, payment, and analytics providers.
________________________________________
1. BPMN Diagram: Return & Refund Processing
Diagram Name: BPMN_ReturnRefundProcessing
This process describes how a customer initiates a product return on the ShopNova platform and how the return is validated, inspected, and refunded through internal systems and the external payment gateway.
Process Elements
Start Event: A customer navigates to their order history and selects "Request Return" on an eligible order item.
Task: Display Return Policy The system presents the applicable return policy for the product category, including the return window (30 days from delivery), condition requirements, and any restocking fees. Non-returnable product categories (e.g., opened software, hygienic items) are flagged.
Task: Collect Return Reason The customer selects a return reason from a predefined list (defective, wrong item, not as described, changed mind, other) and optionally provides a text description. If the product is defective, the customer is prompted to upload supporting photos.
Exclusive Gateway: Within Return Window?
•	Yes → proceed to Submit Return Request.
•	No → proceed to Deny Return Request.
Task: Deny Return Request The system informs the customer that the return window has expired and provides contact information for customer support in case of exceptional circumstances.
End Event Denial: The process ends after the denial notification.
Task: Submit Return Request The system creates a return request record, generates a return authorization number (RMA), and emails a prepaid return shipping label to the customer.
Sub-Process: Process Return & Issue Refund (Decomposed in DFD — see Section 2) The return processing sub-process handles validating the return request against order data, assessing the returned item's condition and eligibility, executing the refund through the payment gateway, and updating all relevant records. This is the sub-process that is decomposed into a Data Flow Diagram.
Exclusive Gateway: Refund Successful?
•	Yes → proceed to Send Refund Confirmation.
•	No → proceed to Escalate to Support.
Task: Escalate to Support If the refund fails (gateway error, disputed transaction, policy exception), the return case is escalated to a customer support agent with full context for manual resolution.
End Event Escalation: The process ends with the case assigned to customer support.
Task: Send Refund Confirmation The system sends a confirmation email and push notification to the customer with the refund amount, expected processing time (3–5 business days), and the original payment method to which the refund was issued.
Task: Update Inventory The returned item is inspected at the warehouse. If in resalable condition, the item is restocked and inventory counts are updated. If damaged, the item is routed to the defective goods workflow.
End Event Successful: Return processed, refund issued, and inventory updated.
________________________________________
2. DFD Diagram: Process Return & Issue Refund
Diagram Name: DFD_ProcessReturnRefund
This Data Flow Diagram decomposes the "Process Return & Issue Refund" sub-process from the BPMN diagram above. It shows how return and refund data flows between external actors, internal processes, and data stores during return validation, eligibility assessment, refund execution, and record updates.
External Entities
EE1: Customer Description: The authenticated end-user who initiated the return request and receives status updates and refund confirmation throughout the process. This is the same Customer entity used in Cases 1, 2, and 3. Trust Boundary: Resides outside both trust boundaries. Threats:
•	T30 — Fraudulent Return Request Spoofing
•	T34 — Return Request Flooding Mitigations:
•	M28 — Return Eligibility Verification Engine
•	M32 — Return Request Throttling
EE2: Payment Gateway Provider (StripeConnect) Description: The external payment processor that processes refund transactions back to the customer's original payment method. This is the same entity used in Case 1 (DFD_ProcessPayment). Trust Boundary: Resides outside both trust boundaries. Threats:
•	T37 — Refund Transaction Data Leakage
•	T35 — Refund Amount Escalation Mitigations:
•	M2 — TLS 1.3 with Certificate Pinning
•	M33 — Refund Amount Validation and Caps
Processes
P12: Validate Return Request Description: Receives the return request from the customer, verifies the RMA number, checks the return window deadline against the original order's delivery date, and validates that the order item exists and has not already been returned. Trust Boundary: Resides inside the Internal Returns Processing Zone. Threats:
•	T30 — Fraudulent Return Request Spoofing
•	T31 — Return Condition Data Tampering Mitigations:
•	M28 — Return Eligibility Verification Engine
•	M4 — Input Validation and Integrity Checks
P13: Assess Return Eligibility Description: Evaluates the returned item's reported condition against the return policy rules, verifies the customer's return history for abuse patterns (e.g., excessive returns), and cross-references the inventory database to confirm the product's return eligibility category. Trust Boundary: Resides inside the Internal Returns Processing Zone. Threats:
•	T31 — Return Condition Data Tampering
•	T36 — Return Record Falsification
•	T30 — Fraudulent Return Request Spoofing Mitigations:
•	M29 — Return Condition Evidence Collection
•	M34 — Return Record Integrity Verification
•	M28 — Return Eligibility Verification Engine
P14: Execute Refund Description: Calculates the refund amount (applying any restocking fees or partial refund rules), sends the refund request to the Payment Gateway Provider, receives the refund confirmation or failure, and records the refund transaction. Trust Boundary: Resides inside the Financial Services Zone. Threats:
•	T35 — Refund Amount Escalation
•	T32 — Refund Repudiation Mitigations:
•	M33 — Refund Amount Validation and Caps
•	M30 — Refund Authorization Workflow
•	M6 — Comprehensive Transaction Logging
P15: Finalize Return Records Description: Updates the return request status to completed, writes the refund details to the customer's order history, updates inventory records for the returned item, and sends the refund confirmation notification to the customer. Trust Boundary: Resides inside the Internal Returns Processing Zone. Threats:
•	T38 — Return Processing Audit Gap
•	T33 — Customer Order History Exposure in Returns Mitigations:
•	M35 — Return Processing Audit Trail
•	M7 — PII Data Masking in Output
Data Stores
DS1: Customer Database Description: Central relational database storing customer profiles, addresses, payment method tokens, and order history. The return process reads order and delivery data to validate return eligibility and writes refund status updates to the customer's order record. Shared across multiple ShopNova subsystems. This is the same data store used in Cases 1 and 2. Trust Boundary: Resides inside the Internal Returns Processing Zone. Threats:
•	T33 — Customer Order History Exposure in Returns
•	T36 — Return Record Falsification Mitigations:
•	M8 — Encryption at Rest with RBAC
•	M31 — Return Data Access Restrictions
•	M34 — Return Record Integrity Verification
DS8: Returns & Refund Records Description: Dedicated data store holding all return request records including RMA numbers, return reasons, item conditions, refund amounts, refund status, and processing timestamps. Supports return analytics and fraud pattern detection. Trust Boundary: Resides inside the Internal Returns Processing Zone. Threats:
•	T36 — Return Record Falsification
•	T32 — Refund Repudiation Mitigations:
•	M34 — Return Record Integrity Verification
•	M11 — Immutable Append-Only Log Storage
DS9: Inventory Database Description: Stores real-time inventory counts, product locations across warehouses, restocking status, and defective goods tracking. The return process queries eligibility rules and updates stock counts upon completed returns. Trust Boundary: Resides inside the Internal Returns Processing Zone. Threats:
•	T31 — Return Condition Data Tampering Mitigations:
•	M29 — Return Condition Evidence Collection
•	M4 — Input Validation and Integrity Checks
DS4: Audit Log Description: Append-only log capturing all return-related events — request submissions, eligibility assessments, refund executions, and record finalizations — for compliance and fraud investigation. Shared across multiple ShopNova subsystems. This is the same data store used in Cases 1, 2, and 3. Trust Boundary: Resides inside the Internal Returns Processing Zone. Threats:
•	T38 — Return Processing Audit Gap
•	T32 — Refund Repudiation Mitigations:
•	M11 — Immutable Append-Only Log Storage
•	M35 — Return Processing Audit Trail
•	M6 — Comprehensive Transaction Logging
Trust Boundaries
TB7: Internal Returns Processing Zone Description: The secured internal zone enclosing ShopNova's return validation services, eligibility assessment logic, record management, and associated data stores. Protected by the API gateway with authentication enforcement and request validation. Handles non-financial return processing operations.
TB8: Financial Services Zone Description: A restricted internal zone dedicated to financial transaction processing, specifically refund calculation and execution. Isolated from the general returns processing zone with additional access controls, transaction signing requirements, and dedicated monitoring. Communication with external payment providers originates exclusively from this zone.
Data Flows
DF35: Return Request Submission Name: Return Request Submission Description: The customer submits a return request containing the RMA number, return reason, item condition description, and optional supporting photos to the Validate Return Request process. Protocol: HTTPS Crosses Trust Boundaries: Yes — from outside into Internal Returns Processing Zone (TB7). From: EE1 (Customer) → P12 (Validate Return Request) Threats:
•	T30 — Fraudulent Return Request Spoofing
•	T34 — Return Request Flooding Mitigations:
•	M28 — Return Eligibility Verification Engine
•	M32 — Return Request Throttling
•	M4 — Input Validation and Integrity Checks
DF36: Customer Order History Query Name: Customer Order History Query Description: The Validate Return Request process queries the Customer Database to retrieve the original order details, delivery date, and item purchase record for return eligibility verification. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Returns Processing Zone (TB7). From: P12 (Validate Return Request) → DS1 (Customer Database)
DF37: Validated Return for Assessment Name: Validated Return for Assessment Description: The validated return request data (confirmed RMA, order match, within return window) is passed from the Validate Return Request process to the Assess Return Eligibility process. Protocol: HTTPS Crosses Trust Boundaries: No — both reside within the Internal Returns Processing Zone (TB7). From: P12 (Validate Return Request) → P13 (Assess Return Eligibility)
DF38: Inventory Eligibility Check Name: Inventory Eligibility Check Description: The Assess Return Eligibility process queries the Inventory Database for the product's return eligibility category (returnable, non-returnable, restocking fee applicable) and current stock levels. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Returns Processing Zone (TB7). From: P13 (Assess Return Eligibility) → DS9 (Inventory Database) Threats:
•	T31 — Return Condition Data Tampering Mitigations:
•	M29 — Return Condition Evidence Collection
DF39: Approved Return for Refund Name: Approved Return for Refund Description: The eligibility-cleared return request with the calculated refund amount and applicable deductions is forwarded from the Assess Return Eligibility process to the Execute Refund process. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Internal Returns Processing Zone (TB7) into Financial Services Zone (TB8). From: P13 (Assess Return Eligibility) → P14 (Execute Refund) Threats:
•	T35 — Refund Amount Escalation Mitigations:
•	M33 — Refund Amount Validation and Caps
DF40: Refund Authorization Request Name: Refund Authorization Request Description: The Execute Refund process sends the refund transaction request (amount, original transaction reference, customer payment token) to the Payment Gateway Provider. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Financial Services Zone (TB8) to outside. From: P14 (Execute Refund) → EE2 (Payment Gateway Provider / StripeConnect) Threats:
•	T37 — Refund Transaction Data Leakage
•	T35 — Refund Amount Escalation Mitigations:
•	M2 — TLS 1.3 with Certificate Pinning
•	M33 — Refund Amount Validation and Caps
DF41: Refund Authorization Response Name: Refund Authorization Response Description: The Payment Gateway Provider returns the refund result (approved, declined, or error) with a refund transaction identifier to the Execute Refund process. Protocol: HTTPS Crosses Trust Boundaries: Yes — from outside into Financial Services Zone (TB8). From: EE2 (Payment Gateway Provider / StripeConnect) → P14 (Execute Refund) Threats:
•	T37 — Refund Transaction Data Leakage Mitigations:
•	M2 — TLS 1.3 with Certificate Pinning
DF42: Refund Confirmation Handoff Name: Refund Confirmation Handoff Description: The Execute Refund process sends the refund outcome (amount, status, transaction ID, timestamp) to the Finalize Return Records process for record updates and customer notification. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Financial Services Zone (TB8) into Internal Returns Processing Zone (TB7). From: P14 (Execute Refund) → P15 (Finalize Return Records)
DF43: Return Record Storage Name: Return Record Storage Description: The Finalize Return Records process writes the completed return and refund details to the Returns & Refund Records data store. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Returns Processing Zone (TB7). From: P15 (Finalize Return Records) → DS8 (Returns & Refund Records) Threats:
•	T36 — Return Record Falsification Mitigations:
•	M34 — Return Record Integrity Verification
DF44: Customer Order History Update Name: Customer Order History Update Description: The Finalize Return Records process updates the customer's order record in the Customer Database with the return status, refund amount, and refund transaction reference. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Returns Processing Zone (TB7). From: P15 (Finalize Return Records) → DS1 (Customer Database) Threats:
•	T33 — Customer Order History Exposure in Returns Mitigations:
•	M31 — Return Data Access Restrictions
DF45: Return Completion Notification Name: Return Completion Notification Description: The Finalize Return Records process sends a refund confirmation notification to the customer with the refund amount, processing timeline, and payment method details (masked). Protocol: HTTPS Crosses Trust Boundaries: Yes — from Internal Returns Processing Zone (TB7) to outside. From: P15 (Finalize Return Records) → EE1 (Customer) Threats:
•	T33 — Customer Order History Exposure in Returns Mitigations:
•	M7 — PII Data Masking in Output
•	M31 — Return Data Access Restrictions
DF46: Return Processing Audit Entry Name: Return Processing Audit Entry Description: The Finalize Return Records process writes a comprehensive audit record capturing the full return lifecycle — validation result, eligibility assessment, refund execution outcome, and record updates — to the Audit Log. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Returns Processing Zone (TB7). From: P15 (Finalize Return Records) → DS4 (Audit Log) Threats:
•	T38 — Return Processing Audit Gap Mitigations:
•	M35 — Return Processing Audit Trail
DF47: Refund Execution Audit Entry Name: Refund Execution Audit Entry Description: The Execute Refund process writes an audit record capturing the refund request, gateway response, transaction reference, and any errors to the Audit Log. Protocol: TLS Crosses Trust Boundaries: Yes — from Financial Services Zone (TB8) into Internal Returns Processing Zone (TB7). From: P14 (Execute Refund) → DS4 (Audit Log) Threats:
•	T32 — Refund Repudiation Mitigations:
•	M6 — Comprehensive Transaction Logging
•	M11 — Immutable Append-Only Log Storage
________________________________________
3. Threat Modeling Diagram: Process Return & Issue Refund Threats
Diagram Name: TM_ProcessReturnRefund
This threat modeling diagram captures the threats and mitigations associated with the DFD_ProcessReturnRefund diagram. Each threat is linked to at least one DFD element and belongs to a threat category from the Threat/Mitigation Categorization diagram (see Section 4).
Threats
T30: Fraudulent Return Request Spoofing Threat Category: Spoofing Risk Level: Critical Likelihood: High Description: An attacker submits return requests using compromised accounts or fabricated RMA numbers, claiming returns for items never purchased or already returned, to fraudulently obtain refunds or replacement products.
T31: Return Condition Data Tampering Threat Category: Tampering Risk Level: High Likelihood: Medium Description: An attacker manipulates the return condition description, supporting photos, or eligibility parameters in transit or at the API level to make a non-eligible return appear eligible (e.g., changing "changed mind" to "defective" to avoid restocking fees).
T32: Refund Repudiation Threat Category: Repudiation Risk Level: Medium Likelihood: Medium Description: A customer or internal actor disputes that a refund was processed or claims the refund amount was incorrect, and the system lacks sufficient transactional evidence to prove the exact refund amount, timing, and authorization chain.
T33: Customer Order History Exposure in Returns Threat Category: Information Disclosure Risk Level: Medium Likelihood: Medium Description: The return processing flow or refund notification inadvertently exposes detailed order history, payment method details, or internal account data beyond what is necessary for the return, enabling profiling or social engineering attacks.
T34: Return Request Flooding Threat Category: Denial of Service Risk Level: Medium Likelihood: High Description: An attacker uses automated scripts to submit a massive volume of return requests, overwhelming the return processing pipeline, consuming customer support resources, and degrading the return experience for legitimate customers.
T35: Refund Amount Escalation Threat Category: Elevation of Privilege Risk Level: Critical Likelihood: Low Description: An attacker manipulates the refund amount by intercepting or modifying the refund request between the eligibility assessment and the payment gateway, escalating a partial refund to a full refund or inflating the amount beyond the original purchase price.
T36: Return Record Falsification Threat Category: Tampering Risk Level: High Likelihood: Low Description: An attacker or malicious insider modifies return records in the Returns & Refund Records data store or the Customer Database to conceal fraudulent returns, alter refund amounts, or fabricate return histories for financial gain.
T37: Refund Transaction Data Leakage Threat Category: Information Disclosure Risk Level: High Likelihood: Low Description: Sensitive refund transaction data (original payment token, refund amount, customer identifier) is exposed during communication with the Payment Gateway Provider due to insufficient transport security or excessive data in API payloads.
T38: Return Processing Audit Gap Threat Category: Repudiation Risk Level: High Likelihood: Low Description: Gaps in the audit trail for the return lifecycle — particularly between eligibility assessment, refund execution, and record finalization — allow return processing steps to occur without a traceable record, enabling undetectable manipulation of the return workflow.
Mitigations
M28: Return Eligibility Verification Engine Mitigation Category: Authentication & Identity Control Type: Preventive Implementation Status: Implemented Cost Type: Medium Cost Value: 18000 Description: Validates every return request against the authenticated customer's order history, delivery confirmation, RMA authenticity, return window, and prior return frequency. Requests that fail any check are rejected with a specific denial code before entering the processing pipeline.
M29: Return Condition Evidence Collection Mitigation Category: Input Validation Control Type: Preventive Implementation Status: Partially Implemented Cost Type: Medium Cost Value: 14000 Description: Requires photographic evidence for defect-based returns, validates image metadata (EXIF timestamps, geolocation plausibility), and stores all submitted evidence immutably alongside the return record for dispute resolution.
M30: Refund Authorization Workflow Mitigation Category: Access Control Control Type: Preventive Implementation Status: Implemented Cost Type: Medium Cost Value: 16000 Description: Refunds above a configurable threshold (currently €100) require secondary authorization from a supervisor or automated rule engine before submission to the payment gateway. All authorization decisions are logged with the approving principal and timestamp.
M31: Return Data Access Restrictions Mitigation Category: Data Protection Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 5000 Description: The return processing services access only the minimum required fields from the Customer Database (order ID, delivery date, item reference, payment token). Full customer profile data, browsing history, and unrelated order details are excluded from return processing queries.
M32: Return Request Throttling Mitigation Category: Availability & Resilience Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 3500 Description: Enforces per-customer rate limits on return requests (maximum 3 per day, 10 per month) and per-IP limits for unauthenticated RMA lookups, with progressive CAPTCHA challenges at 50% of thresholds.
M33: Refund Amount Validation and Caps Mitigation Category: Input Validation Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 4000 Description: The refund amount is independently recalculated from the original order record immediately before gateway submission and compared against the amount passed from the eligibility step. Any discrepancy blocks the refund. A hard cap prevents refunds exceeding the original transaction amount.
M34: Return Record Integrity Verification Mitigation Category: Data Protection Control Type: Detective Implementation Status: Implemented Cost Type: Medium Cost Value: 10000 Description: Every return record includes a cryptographic hash of the key fields (RMA, order ID, refund amount, status) computed at creation and verified on every subsequent read or update, enabling detection of unauthorized modifications.
M35: Return Processing Audit Trail Mitigation Category: Logging & Monitoring Control Type: Detective Implementation Status: Implemented Cost Type: Low Cost Value: 5000 Description: Every state transition in the return lifecycle (submitted → validated → assessed → refunded → finalized) is logged as an individual audit event with the processing service identity, input data hash, decision outcome, and cryptographically signed timestamp.
Threat-to-Mitigation Mapping — Case 4 (Process Return & Issue Refund)
T30: Fraudulent Return Request Spoofing → M28 (Return Eligibility Verification Engine), M4 (Input Validation and Integrity Checks) 
T31: Return Condition Data Tampering → M29 (Return Condition Evidence Collection), M4 (Input Validation and Integrity Checks) 
T32: Refund Repudiation → M6 (Comprehensive Transaction Logging), M30 (Refund Authorization Workflow), M11 (Immutable Append-Only Log Storage) 
T33: Customer Order History Exposure in Returns → M31 (Return Data Access Restrictions), M7 (PII Data Masking in Output) 
T34: Return Request Flooding → M32 (Return Request Throttling) 
T35: Refund Amount Escalation → M33 (Refund Amount Validation and Caps), M30 (Refund Authorization Workflow) 
T36: Return Record Falsification → M34 (Return Record Integrity Verification), M8 (Encryption at Rest with RBAC) 
T37: Refund Transaction Data Leakage → M2 (TLS 1.3 with Certificate Pinning) 
T38: Return Processing Audit Gap → M35 (Return Processing Audit Trail), M11 (Immutable Append-Only Log Storage)

Case 5/5 — Shipping & Delivery Tracking
Organization: ShopNova — a fictional mid-size e-commerce company selling consumer electronics and accessories. ShopNova operates a web storefront, mobile app, and integrates with third-party logistics, payment, and analytics providers.
________________________________________
1. BPMN Diagram: Shipping & Delivery Tracking
Diagram Name: BPMN_ShippingDeliveryTracking
This process describes how ShopNova receives shipment tracking updates from the logistics carrier, correlates them with customer orders, generates delivery milestone events, and notifies customers of their order's delivery progress.
Process Elements
Start Event: The shipping carrier transmits a tracking status update via webhook for a ShopNova shipment.
Task: Receive Carrier Webhook The system receives an inbound tracking event from the logistics carrier's API. The event payload includes the tracking number, shipment status code, timestamp, location, and carrier-specific metadata.
Task: Authenticate Carrier Source The system verifies the webhook signature, validates the carrier's API key, and confirms the source IP against the allowlisted carrier network ranges. Unauthenticated or malformed payloads are rejected and logged.
Sub-Process: Process Tracking Update & Notify Customer (Decomposed in DFD — see Section 2) The tracking sub-process handles validating the tracking data format, correlating the update with the correct ShopNova order, updating the shipment status in the order database, generating delivery milestone events, and dispatching notifications to the customer. This is the sub-process that is decomposed into a Data Flow Diagram.
Exclusive Gateway: Delivery Confirmed?
•	Yes → proceed to Close Shipment.
•	No → proceed to Await Next Update.
Task: Await Next Update The system returns to a waiting state for the next carrier webhook event for this shipment. If no update is received within the expected SLA window, an alert is generated for the logistics operations team.
End Event Waiting: The process pauses until the next carrier event.
Task: Close Shipment Upon confirmed delivery, the system marks the shipment record as completed, triggers the post-delivery customer experience flow (e.g., review prompt, satisfaction survey), and archives the tracking history.
Task: Log Delivery Completion All shipment lifecycle events from pickup to delivery are consolidated into a final audit record, including total transit time, number of status updates received, and any delivery exceptions encountered.
End Event Successful: Shipment delivered and tracking lifecycle closed.
________________________________________
2. DFD Diagram: Process Tracking Update & Notify Customer
Diagram Name: DFD_ProcessTrackingNotify
This Data Flow Diagram decomposes the "Process Tracking Update & Notify Customer" sub-process from the BPMN diagram above. It shows how tracking data flows from the carrier through internal processing and out to the customer as delivery notifications.
External Entities
EE1: Customer Description: The authenticated end-user who receives delivery status notifications and can view shipment tracking details through the ShopNova web storefront or mobile app. This is the same Customer entity used in Cases 1, 2, 3, and 4. Trust Boundary: Resides outside all trust boundaries. Threats:
•	T46 — Notification Content Spoofing Mitigations:
•	M42 — Notification Origin Verification
EE6: Shipping Carrier (LogiTrack) Description: The third-party logistics carrier that transports ShopNova packages and provides real-time tracking updates via webhook API. LogiTrack transmits shipment events including pickup, in-transit, out-for-delivery, delivered, and exception statuses. Trust Boundary: Resides outside all trust boundaries. Threats:
•	T39 — Carrier Identity Spoofing
•	T43 — Tracking Update Flooding Mitigations:
•	M36 — Carrier API Key Authentication and IP Allowlisting
•	M40 — Tracking Update Rate Limiting
Processes
P16: Ingest and Validate Carrier Update Description: Receives the raw tracking event from the shipping carrier's webhook, validates the payload schema (required fields, status code enumeration, timestamp format), verifies the carrier's API key and source IP, and normalizes the data into ShopNova's internal tracking format. Trust Boundary: Resides inside the Carrier Integration Zone. Threats:
•	T39 — Carrier Identity Spoofing
•	T40 — Shipment Tracking Data Tampering
•	T44 — Carrier API Privilege Escalation Mitigations:
•	M36 — Carrier API Key Authentication and IP Allowlisting
•	M37 — Tracking Data Schema Validation
•	M41 — Carrier API Scope Enforcement
P17: Correlate and Update Shipment Status Description: Matches the validated tracking event to the corresponding ShopNova order by looking up the tracking number in the Order & Shipment Database, updates the shipment status and location fields, and forwards the update to the milestone generation process. Trust Boundary: Resides inside the Internal Order Management Zone. Threats:
•	T40 — Shipment Tracking Data Tampering
•	T45 — Order Status Record Tampering Mitigations:
•	M37 — Tracking Data Schema Validation
•	M4 — Input Validation and Integrity Checks
P18: Generate Delivery Milestone Description: Interprets the shipment status update and generates structured delivery milestone events (picked up, in transit, out for delivery, delivered, delivery exception). For delivery confirmations, captures proof-of-delivery metadata (signature status, photo reference, delivery timestamp). Triggers notification dispatch for customer-facing milestones. Trust Boundary: Resides inside the Internal Order Management Zone. Threats:
•	T41 — Delivery Confirmation Repudiation
•	T42 — Customer Delivery Address Exposure Mitigations:
•	M38 — Delivery Confirmation Evidence Chain
•	M39 — Address Data Minimization in Transit
•	M43 — End-to-End Delivery Audit Trail
P19: Dispatch Delivery Notification Description: Retrieves the customer's notification preferences (email, push, SMS, quiet hours), composes the delivery status message with masked address details and a tracking link, and dispatches it through the appropriate channel. Trust Boundary: Resides inside the Notification Dispatch Zone. Threats:
•	T46 — Notification Content Spoofing
•	T42 — Customer Delivery Address Exposure Mitigations:
•	M42 — Notification Origin Verification
•	M7 — PII Data Masking in Output
Data Stores
DS10: Order and Shipment Database Description: Stores order records with associated shipment details including tracking numbers, carrier references, shipment status history, delivery addresses, and proof-of-delivery metadata. Supports order-to-shipment correlation queries and status history retrieval. Trust Boundary: Resides inside the Internal Order Management Zone. Threats:
•	T45 — Order Status Record Tampering
•	T42 — Customer Delivery Address Exposure Mitigations:
•	M8 — Encryption at Rest with RBAC
•	M4 — Input Validation and Integrity Checks
DS4: Audit Log Description: Append-only log capturing all tracking events, milestone generations, notification dispatches, and carrier authentication outcomes for compliance and dispute resolution. Shared across multiple ShopNova subsystems. This is the same data store used in Cases 1, 2, 3, and 4. Trust Boundary: Resides inside the Internal Order Management Zone. Threats:
•	T47 — Delivery Audit Trail Gaps
•	T41 — Delivery Confirmation Repudiation Mitigations:
•	M11 — Immutable Append-Only Log Storage
•	M6 — Comprehensive Transaction Logging
•	M43 — End-to-End Delivery Audit Trail
DS11: Notification Preferences Description: Stores customer notification channel preferences (email enabled, push enabled, SMS opt-in), quiet hours configuration, and delivery notification granularity settings (all milestones vs. delivery-only). Referenced by the notification dispatch process to respect customer communication choices. Trust Boundary: Resides inside the Notification Dispatch Zone. Threats:
•	T42 — Customer Delivery Address Exposure Mitigations:
•	M39 — Address Data Minimization in Transit
Trust Boundaries
TB9: Carrier Integration Zone Description: An isolated ingestion zone that receives and validates inbound data from external shipping carriers. Enforces API key authentication, IP allowlisting, payload schema validation, and rate limiting before any carrier data enters the internal order management systems. Acts as a controlled gateway between untrusted carrier networks and ShopNova's internal infrastructure.
TB10: Internal Order Management Zone Description: The core internal zone enclosing ShopNova's order processing services, shipment tracking logic, milestone generation, and associated data stores. Protected by internal service mesh authentication and network-level segmentation from the carrier integration zone and external networks.
TB11: Notification Dispatch Zone Description: A dedicated zone for composing and dispatching outbound customer notifications. Isolated from the order management zone to enforce data minimization — only the information strictly required for notification composition (customer ID, notification preferences, masked delivery details) is passed into this zone.
Data Flows
DF48: Carrier Tracking Update Name: Carrier Tracking Update Description: The shipping carrier transmits a tracking event payload (tracking number, status code, timestamp, location, carrier metadata) to the Ingest and Validate Carrier Update process via webhook. Protocol: HTTPS Crosses Trust Boundaries: Yes — from outside into Carrier Integration Zone (TB9). From: EE6 (Shipping Carrier / LogiTrack) → P16 (Ingest and Validate Carrier Update) Threats:
•	T39 — Carrier Identity Spoofing
•	T40 — Shipment Tracking Data Tampering Mitigations:
•	M36 — Carrier API Key Authentication and IP Allowlisting
•	M37 — Tracking Data Schema Validation
DF49: Tracking Receipt Acknowledgment Name: Tracking Receipt Acknowledgment Description: The Ingest and Validate Carrier Update process returns an HTTP acknowledgment (200 OK or error code) to the shipping carrier confirming receipt or rejection of the tracking event. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Carrier Integration Zone (TB9) to outside. From: P16 (Ingest and Validate Carrier Update) → EE6 (Shipping Carrier / LogiTrack)
DF50: Validated Tracking Data Name: Validated Tracking Data Description: The validated and normalized tracking event is forwarded from the Ingest and Validate Carrier Update process to the Correlate and Update Shipment Status process for order matching. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Carrier Integration Zone (TB9) into Internal Order Management Zone (TB10). From: P16 (Ingest and Validate Carrier Update) → P17 (Correlate and Update Shipment Status) Threats:
•	T40 — Shipment Tracking Data Tampering Mitigations:
•	M37 — Tracking Data Schema Validation
DF51: Order Record Retrieval Name: Order Record Retrieval Description: The Correlate and Update Shipment Status process queries the Order & Shipment Database to find the order matching the tracking number and retrieve the current shipment status. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Order Management Zone (TB10). From: DS10 (Order & Shipment Database) → P17 (Correlate and Update Shipment Status)
DF52: Shipment Status Update Name: Shipment Status Update Description: The Correlate and Update Shipment Status process writes the new shipment status, location, and timestamp to the Order & Shipment Database, appending to the shipment's status history. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Order Management Zone (TB10). From: P17 (Correlate and Update Shipment Status) → DS10 (Order & Shipment Database) Threats:
•	T45 — Order Status Record Tampering Mitigations:
•	M4 — Input Validation and Integrity Checks
DF53: Delivery Milestone Event Name: Delivery Milestone Event Description: The Correlate and Update Shipment Status process forwards the shipment update to the Generate Delivery Milestone process for milestone classification and proof-of-delivery handling. Protocol: HTTPS Crosses Trust Boundaries: No — both reside within the Internal Order Management Zone (TB10). From: P17 (Correlate and Update Shipment Status) → P18 (Generate Delivery Milestone)
DF54: Notification Trigger Name: Notification Trigger Description: The Generate Delivery Milestone process sends a notification request containing the customer ID, milestone type, and minimized delivery details (city-level location, no full address) to the Dispatch Delivery Notification process. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Internal Order Management Zone (TB10) into Notification Dispatch Zone (TB11). From: P18 (Generate Delivery Milestone) → P19 (Dispatch Delivery Notification) Threats:
•	T42 — Customer Delivery Address Exposure Mitigations:
•	M39 — Address Data Minimization in Transit
DF55: Customer Notification Preferences Name: Customer Notification Preferences Description: The Dispatch Delivery Notification process queries the Notification Preferences data store to retrieve the customer's preferred notification channels, quiet hours, and milestone granularity settings. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Notification Dispatch Zone (TB11). From: DS11 (Notification Preferences) → P19 (Dispatch Delivery Notification)
DF56: Delivery Status Notification Name: Delivery Status Notification Description: The Dispatch Delivery Notification process sends the composed delivery status message to the customer through their preferred channel (email, push notification, or SMS) with masked address details and a tracking page link. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Notification Dispatch Zone (TB11) to outside. From: P19 (Dispatch Delivery Notification) → EE1 (Customer) Threats:
•	T46 — Notification Content Spoofing
•	T42 — Customer Delivery Address Exposure Mitigations:
•	M42 — Notification Origin Verification
•	M7 — PII Data Masking in Output
DF57: Carrier Update Audit Entry Name: Carrier Update Audit Entry Description: The Ingest and Validate Carrier Update process writes an audit record capturing every inbound carrier event — including accepted and rejected payloads, carrier identity verification result, and source IP — to the Audit Log. Protocol: TLS Crosses Trust Boundaries: Yes — from Carrier Integration Zone (TB9) into Internal Order Management Zone (TB10). From: P16 (Ingest and Validate Carrier Update) → DS4 (Audit Log) Threats:
•	T47 — Delivery Audit Trail Gaps Mitigations:
•	M43 — End-to-End Delivery Audit Trail
DF58: Milestone Audit Entry Name: Milestone Audit Entry Description: The Generate Delivery Milestone process writes an audit record for each milestone event generated, including the milestone type, proof-of-delivery metadata (if delivery confirmation), and timestamp. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Order Management Zone (TB10). From: P18 (Generate Delivery Milestone) → DS4 (Audit Log) Threats:
•	T41 — Delivery Confirmation Repudiation Mitigations:
•	M38 — Delivery Confirmation Evidence Chain
________________________________________
3. Threat Modeling Diagram: Process Tracking Update & Notify Customer Threats
Diagram Name: TM_ProcessTrackingNotify
This threat modeling diagram captures the threats and mitigations associated with the DFD_ProcessTrackingNotify diagram. Each threat is linked to at least one DFD element and belongs to a threat category from the Threat/Mitigation Categorization diagram (see Section 4).
Threats
T39: Carrier Identity Spoofing Threat Category: Spoofing Risk Level: Critical Likelihood: Medium Description: An attacker impersonates the legitimate shipping carrier by forging webhook requests with fabricated API keys or replaying captured carrier payloads, injecting false tracking updates (e.g., marking packages as delivered when they are not) to facilitate package theft or disrupt customer trust.
T40: Shipment Tracking Data Tampering Threat Category: Tampering Risk Level: High Likelihood: Medium Description: An attacker modifies tracking event payloads in transit between the carrier and ShopNova's ingestion endpoint, altering shipment status codes, delivery timestamps, or location data to misrepresent delivery progress or cover logistics fraud.
T41: Delivery Confirmation Repudiation Threat Category: Repudiation Risk Level: Medium Likelihood: Medium Description: A customer disputes that a package was delivered despite the carrier's delivery confirmation, and the system lacks sufficient proof-of-delivery evidence (signature capture, photo, GPS coordinates, timestamp) to resolve the dispute conclusively.
T42: Customer Delivery Address Exposure Threat Category: Information Disclosure Risk Level: High Likelihood: Medium Description: The tracking update processing or notification flow exposes the customer's full delivery address in API responses, notification content, or internal logs beyond what is necessary for the operation, enabling address harvesting or physical security risks.
T43: Tracking Update Flooding Threat Category: Denial of Service Risk Level: Medium Likelihood: High Description: An attacker floods the carrier webhook endpoint with a massive volume of tracking events (legitimate or fabricated), overwhelming the ingestion pipeline, consuming processing resources, and delaying legitimate tracking updates from reaching customers.
T44: Carrier API Privilege Escalation Threat Category: Elevation of Privilege Risk Level: High Likelihood: Low Description: A compromised or malicious carrier API key is used to access endpoints beyond the tracking update scope, such as querying customer order details, modifying shipment records, or accessing other carriers' tracking data, exploiting insufficient API scope enforcement.
T45: Order Status Record Tampering Threat Category: Tampering Risk Level: High Likelihood: Low Description: An attacker or malicious insider directly modifies shipment status records in the Order & Shipment Database, fabricating delivery confirmations, altering delivery dates, or deleting exception records to conceal logistics issues or facilitate fraud.
T46: Notification Content Spoofing Threat Category: Spoofing Risk Level: Medium Likelihood: Low Description: An attacker sends fake delivery notification emails or push notifications that mimic ShopNova's branding and format, directing customers to phishing pages for credential harvesting or payment information theft under the guise of delivery updates.
T47: Delivery Audit Trail Gaps Threat Category: Repudiation Risk Level: High Likelihood: Low Description: Gaps in the audit trail between carrier update ingestion, milestone generation, and notification dispatch make it impossible to reconstruct the full lifecycle of a delivery event, undermining dispute resolution and enabling undetectable manipulation of the delivery workflow.
Mitigations
M36: Carrier API Key Authentication and IP Allowlisting Mitigation Category: Authentication & Identity Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 5000 Description: Every inbound carrier webhook request must include a valid HMAC-signed API key in the authorization header. The source IP is validated against the carrier's registered IP ranges. Requests failing either check are rejected with a 403 response and logged as security events.
M37: Tracking Data Schema Validation Mitigation Category: Input Validation Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 3000 Description: All inbound tracking payloads are validated against a strict JSON schema enforcing required fields, status code enumeration, ISO 8601 timestamp format, and maximum field lengths. Payloads failing schema validation are rejected before any processing occurs.
M38: Delivery Confirmation Evidence Chain Mitigation Category: Logging & Monitoring Control Type: Detective Implementation Status: Partially Implemented Cost Type: Medium Cost Value: 12000 Description: For delivery confirmation events, the system captures and stores the carrier's proof-of-delivery metadata (signature image reference, delivery photo URL, GPS coordinates, timestamp) alongside the milestone record, creating a verifiable evidence chain for dispute resolution.
M39: Address Data Minimization in Transit Mitigation Category: Data Protection Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 2500 Description: Delivery notifications and cross-zone data flows include only city-level location information. Full delivery addresses are never transmitted to the Notification Dispatch Zone or included in customer-facing notifications. Address details remain accessible only within the Internal Order Management Zone.
M40: Tracking Update Rate Limiting Mitigation Category: Availability & Resilience Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 3000 Description: The carrier webhook endpoint enforces per-carrier and per-IP rate limits (maximum 1000 events per minute per carrier, 100 per minute per IP), with automatic throttling and queueing for bursts, preventing ingestion pipeline saturation from floods.
M41: Carrier API Scope Enforcement Mitigation Category: Access Control Control Type: Preventive Implementation Status: Implemented Cost Type: Medium Cost Value: 8000 Description: Carrier API keys are scoped to a strict allowlist of permitted operations (tracking update submission and acknowledgment receipt only). Any attempt to access order query, record modification, or cross-carrier endpoints is blocked and triggers a security alert.
M42: Notification Origin Verification Mitigation Category: Network Security Control Type: Preventive Implementation Status: Implemented Cost Type: Low Cost Value: 4000 Description: All outbound delivery notifications include DKIM signatures, SPF records, and DMARC enforcement for email, and cryptographic signing for push notifications, enabling customers' mail clients and devices to verify that notifications genuinely originate from ShopNova.
M43: End-to-End Delivery Audit Trail Mitigation Category: Logging & Monitoring Control Type: Detective Implementation Status: Implemented Cost Type: Medium Cost Value: 9000 Description: Every step of the delivery tracking lifecycle — carrier ingestion, order correlation, milestone generation, notification dispatch — is logged as a linked audit chain with correlation IDs, enabling end-to-end reconstruction of any delivery event from carrier webhook to customer notification.
Threat-to-Mitigation Mapping — Case 5 (Process Tracking Update & Notify Customer)
T39: Carrier Identity Spoofing → M36 (Carrier API Key Authentication and IP Allowlisting), M41 (Carrier API Scope Enforcement) 
T40: Shipment Tracking Data Tampering → M37 (Tracking Data Schema Validation), M4 (Input Validation and Integrity Checks) 
T41: Delivery Confirmation Repudiation → M38 (Delivery Confirmation Evidence Chain), M43 (End-to-End Delivery Audit Trail) 
T42: Customer Delivery Address Exposure → M39 (Address Data Minimization in Transit), M7 (PII Data Masking in Output) 
T43: Tracking Update Flooding → M40 (Tracking Update Rate Limiting) 
T44: Carrier API Privilege Escalation → M41 (Carrier API Scope Enforcement), M36 (Carrier API Key Authentication and IP Allowlisting) 
T45: Order Status Record Tampering → M4 (Input Validation and Integrity Checks), M8 (Encryption at Rest with RBAC) 
T46: Notification Content Spoofing → M42 (Notification Origin Verification) 
T47: Delivery Audit Trail Gaps → M43 (End-to-End Delivery Audit Trail), M11 (Immutable Append-Only Log Storage), M6 (Comprehensive Transaction Logging)"""

text_description_owasp = """
Case 1/2 — Patient Admission & Medical Records
Domain: MedTrack General Hospital — a mid-size regional hospital operating an integrated IT infrastructure that includes a patient portal, electronic health record system, insurance verification services, and clinical workstations. The hospital serves approximately 200,000 patients annually and must comply with HIPAA regulations.
________________________________________
1. DFD Diagram: Patient Admission & Medical Records
Diagram Name: DFD_PatientAdmissionRecords
This Data Flow Diagram models how patient data flows during the admission process — from initial patient registration through insurance verification, clinical record creation, and discharge summary generation.
________________________________________
Trust Boundaries
TB1: Hospital Perimeter Network (DMZ) Description: The externally facing network zone that hosts the patient portal, API gateways, and insurance verification interfaces. All inbound traffic from patients, referring physicians, and insurance providers enters through this zone and is subjected to TLS termination, authentication enforcement, and request validation before being forwarded to the internal clinical network.
TB2: Internal Clinical Network Description: The secured internal network enclosing the hospital's clinical application servers, electronic health records database, insurance claims repository, and audit systems. Access is restricted to authenticated clinical workstations and authorized internal services. Network segmentation and endpoint protection enforce strict access boundaries.
________________________________________
External Entities
EE1: Patient Description: An individual seeking medical care who interacts with the hospital's patient portal via a web browser or mobile application to submit registration information, upload identification documents, view appointment schedules, and access their medical records. Trust Boundary: Resides outside the Hospital Perimeter Network (DMZ) — in the untrusted external zone.
Susceptible Threats:
T1: Patient Identity Spoofing Threat Category: Spoofing Risk Level: Critical Likelihood: High Severity: Critical Score: 8.5 Description: An attacker impersonates a legitimate patient by using stolen credentials, forged identity documents, or compromised session tokens to access the patient portal, view sensitive medical records, or register under a false identity to obtain fraudulent medical services.
Mitigations for T1:
•	M1: Multi-Factor Patient Authentication Mitigation Category: Authentication & Identity Description: Enforces multi-factor authentication (password + SMS OTP or authenticator app) for all patient portal logins and sensitive operations such as viewing medical records or updating personal information.
•	M2: Biometric Identity Verification at Registration Mitigation Category: Authentication & Identity Description: Requires patients to verify their identity through government-issued photo ID scanning with facial comparison at the point of in-person registration, creating a verified identity anchor for the digital account.
T2: Patient Action Repudiation Threat Category: Repudiation Risk Level: Medium Likelihood: Medium Severity: Medium Score: 5.0 Description: A patient denies having submitted a registration form, signed a consent document, or authorized the release of medical records through the portal, and the system lacks sufficient audit evidence to prove the patient performed the action.
Mitigations for T2:
•	M3: Patient Action Audit Trail with Digital Signatures Mitigation Category: Logging & Monitoring Description: Every patient-initiated action (registration, consent submission, record access, document upload) is logged with a cryptographically signed timestamp, session identifier, IP address, and device fingerprint, creating non-repudiable evidence of the action.
________________________________________
EE2: Referring Physician Description: An external healthcare provider (e.g., a general practitioner from an affiliated clinic) who submits patient referral letters, transfers clinical notes, and requests admission on behalf of a patient through the hospital's physician referral API. Trust Boundary: Resides outside the Hospital Perimeter Network (DMZ) — in the untrusted external zone.
Susceptible Threats:
T3: Physician Identity Spoofing Threat Category: Spoofing Risk Level: High Likelihood: Medium Severity: High Score: 7.2 Description: An attacker impersonates a legitimate referring physician by using stolen API credentials or a compromised clinic workstation to submit fraudulent referral letters, access patient records outside their authorized scope, or admit patients under false medical pretenses.
Mitigations for T3:
•	M4: Physician Mutual TLS and Certificate Authentication Mitigation Category: Authentication & Identity Description: All physician referral API connections require mutual TLS authentication using X.509 certificates issued by the hospital's trusted certificate authority, ensuring that only registered and verified physician endpoints can establish connections.
•	M5: Physician API Key Rotation and Scope Restriction Mitigation Category: Access Control Description: Physician API keys are scoped to specific permitted operations (referral submission, limited patient record read), automatically rotated every 90 days, and bound to registered clinic IP ranges. Any out-of-scope access attempt is blocked and triggers a security alert.
________________________________________
EE3: Insurance Provider Description: An external insurance company that receives eligibility verification requests, processes pre-authorization inquiries, and returns coverage details and co-payment amounts through a standardized API (HL7 FHIR-based). Trust Boundary: Resides outside the Hospital Perimeter Network (DMZ) — in the untrusted external zone.
Susceptible Threats:
T4: Insurance Provider Spoofing Threat Category: Spoofing Risk Level: High Likelihood: Low Severity: High Score: 6.4 Description: An attacker intercepts or impersonates the insurance provider's API endpoint, returning fabricated eligibility confirmations or coverage amounts that lead the hospital to admit patients under incorrect insurance assumptions, causing financial losses or treatment denials.
Mitigations for T4:
•	M6: Insurance API Endpoint Certificate Pinning Mitigation Category: Network Security Description: The hospital's insurance verification client pins the insurance provider's TLS certificate fingerprint and validates it on every connection, preventing man-in-the-middle attacks and endpoint impersonation even if a CA is compromised.
T5: Insurance Communication Repudiation Threat Category: Repudiation Risk Level: Medium Likelihood: Medium Severity: Medium Score: 5.5 Description: The insurance provider disputes that a pre-authorization was granted or claims the coverage terms communicated were different from what the hospital received, and the system lacks non-repudiable records of the original API exchange.
Mitigations for T5:
•	M7: Insurance Transaction Logging with Message Signing Mitigation Category: Logging & Monitoring Description: All insurance API requests and responses are logged with their complete payloads and cryptographically signed by both parties (using JWS), creating a non-repudiable record of every eligibility check and pre-authorization exchange.
________________________________________
Processes
P1: Patient Registration Gateway Description: Receives patient registration submissions from the patient portal, validates demographic data (name, date of birth, contact information, identification documents), checks for duplicate records in the EHR database, and creates or updates the patient's master record. Trust Boundary: Resides inside the Hospital Perimeter Network (DMZ).
Susceptible Threats:
T6: Registration Data Tampering Threat Category: Tampering Risk Level: High Likelihood: Medium Severity: High Score: 7.0 Description: An attacker intercepts and modifies patient registration data in transit between the patient portal and the registration gateway, altering demographic details, insurance policy numbers, or contact information to facilitate medical identity theft or insurance fraud.
Mitigations for T6:
•	M8: Server-Side Registration Data Validation Mitigation Category: Input Validation Description: The registration gateway applies strict server-side validation on all submitted fields — format checks on dates and phone numbers, cross-referencing identification numbers against government databases, and integrity hash verification on the submitted payload.
•	M9: End-to-End Encryption for Registration Payloads Mitigation Category: Network Security Description: Registration data is encrypted at the application layer (JWE) in addition to TLS transport encryption, ensuring data integrity and confidentiality even if TLS termination at the DMZ is compromised.
T7: Patient Record Information Disclosure Threat Category: Information Disclosure Risk Level: Critical Likelihood: Medium Severity: Critical Score: 8.8 Description: The registration gateway inadvertently exposes patient PII (Social Security numbers, insurance details, medical identifiers) through verbose error messages, debug logs, or overly detailed API responses to unauthorized callers.
Mitigations for T7:
•	M10: Structured Error Responses without PII Leakage Mitigation Category: Data Protection Description: Error responses from the registration gateway use generic error codes and messages. All PII is stripped from logs, stack traces are suppressed in production, and API responses return only the minimum fields required by the caller's authorization level.
T8: Registration Service Denial of Service Threat Category: Denial of Service Risk Level: Medium Likelihood: High Severity: Medium Score: 6.0 Description: An attacker floods the patient registration endpoint with a massive volume of requests, overwhelming the gateway and preventing legitimate patients from completing registration, potentially disrupting hospital admissions during peak hours.
Mitigations for T8:
•	M11: Registration Endpoint Rate Limiting and WAF Rules Mitigation Category: Availability & Resilience Description: The registration endpoint enforces per-IP and per-session rate limits with progressive CAPTCHA challenges, backed by a web application firewall that detects and blocks automated abuse patterns and volumetric attacks.
________________________________________
P2: Verify Insurance Eligibility Description: Takes the patient's insurance policy details from the registration record, sends an eligibility verification request to the external Insurance Provider API, receives the coverage response, and updates the patient's admission record with verified insurance status, co-payment amounts, and pre-authorization codes. Trust Boundary: Resides inside the Hospital Perimeter Network (DMZ).
Susceptible Threats:
T9: Insurance Data Tampering in Transit Threat Category: Tampering Risk Level: High Likelihood: Medium Severity: High Score: 7.4 Description: An attacker modifies insurance eligibility responses in transit between the Insurance Provider and the Verify Insurance Eligibility process, altering coverage amounts, pre-authorization codes, or co-payment values to inflate or falsify the patient's coverage.
Mitigations for T9:
•	M12: FHIR Message Integrity Validation Mitigation Category: Input Validation Description: All inbound HL7 FHIR messages from the insurance provider include a digital signature (using JWS with RS256) that is validated by the eligibility verification process before any data is accepted, detecting any in-transit modification.
T10: Eligibility Process Elevation of Privilege Threat Category: Elevation of Privilege Risk Level: High Likelihood: Low Severity: Critical Score: 7.8 Description: An attacker exploits a vulnerability in the insurance eligibility verification process to escalate from the limited DMZ service account to an internal clinical network account, gaining unauthorized access to the EHR database or other internal resources.
Mitigations for T10:
•	M13: DMZ Service Account Isolation and Least Privilege Mitigation Category: Access Control Description: The insurance eligibility process runs under a dedicated service account with minimal permissions — read access to patient insurance fields only, write access limited to eligibility status updates. The account cannot access clinical records, cannot initiate connections to the internal clinical network, and runs in a containerized environment with no shell access.
________________________________________
P3: Manage Clinical Records Description: Core clinical records management process that creates, reads, updates, and archives patient medical records in the EHR Database. Handles admission notes, diagnosis codes, treatment plans, medication orders, lab results, and attending physician assignments. Enforces role-based access control based on the clinical staff member's role and treating relationship with the patient. Trust Boundary: Resides inside the Internal Clinical Network.
Susceptible Threats:
T11: Unauthorized Clinical Record Modification Threat Category: Tampering Risk Level: Critical Likelihood: Medium Severity: Critical Score: 9.0 Description: An attacker or malicious insider modifies clinical records — altering diagnosis codes, medication dosages, lab results, or treatment plans — to conceal medical errors, commit insurance fraud, or endanger patient safety through incorrect medical information.
Mitigations for T11:
•	M14: Clinical Record Versioning with Change Tracking Mitigation Category: Data Protection Description: Every modification to a clinical record creates a new version with the previous version preserved immutably. Each change is tagged with the authenticated clinician's identity, timestamp, workstation ID, and a mandatory change reason field, enabling full reconstruction of the record's history.
•	M15: Dual Authorization for Critical Record Changes Mitigation Category: Access Control Description: Changes to critical clinical fields (diagnosis codes, medication orders, allergy information) require dual authorization — the initiating clinician and a supervising physician must both approve the change before it is committed to the EHR.
T12: Clinical Record Access Repudiation Threat Category: Repudiation Risk Level: Medium Likelihood: Medium Severity: High Score: 6.2 Description: A clinical staff member accesses patient records without a legitimate treating relationship (e.g., viewing a celebrity's medical records out of curiosity) and denies having done so, and the system lacks sufficiently granular audit evidence to prove the access occurred.
Mitigations for T12:
•	M16: Break-the-Glass Access Logging Mitigation Category: Logging & Monitoring Description: All clinical record access events are logged with the clinician's identity, the patient record accessed, timestamp, workstation, and access justification. Access to records outside the clinician's assigned patient list triggers a break-the-glass workflow requiring a documented reason and generating an alert to the compliance team.
T13: Patient Data Exfiltration Threat Category: Information Disclosure Risk Level: Critical Likelihood: Medium Severity: Critical Score: 9.2 Description: An attacker gains access to the Manage Clinical Records process and extracts bulk patient data (medical histories, diagnoses, medications, SSNs) through API abuse, SQL injection, or exploitation of an over-privileged service account, leading to a HIPAA breach.
Mitigations for T13:
•	M17: Data Loss Prevention and Anomalous Query Detection Mitigation Category: Data Protection Description: A data loss prevention layer monitors all data egress from the clinical records process, detecting and blocking bulk data extraction attempts, unusually large result sets, and query patterns inconsistent with normal clinical workflows. Alerts are generated for queries exceeding configurable row-count thresholds.
________________________________________
P4: Generate Discharge Summary Description: Compiles the patient's admission record, treatment history, medications administered, lab results, and follow-up instructions into a structured discharge summary. The summary is stored in the EHR, sent to the patient via the portal, and transmitted to the referring physician if applicable. Trust Boundary: Resides inside the Internal Clinical Network.
Susceptible Threats:
T14: Discharge Summary Tampering Threat Category: Tampering Risk Level: High Likelihood: Low Severity: High Score: 6.8 Description: An attacker or insider modifies the discharge summary after generation — altering medication instructions, follow-up schedules, or diagnosis information — before it reaches the patient or referring physician, potentially endangering post-discharge care.
Mitigations for T14:
•	M18: Discharge Summary Digital Signing Mitigation Category: Data Protection Description: Each generated discharge summary is digitally signed by the discharging physician's certificate. Any modification after signing invalidates the signature, and recipients (patient portal, referring physician API) verify the signature before displaying or processing the document.
T15: PHI Exposure in Discharge Notifications Threat Category: Information Disclosure Risk Level: High Likelihood: Medium Severity: High Score: 7.5 Description: The discharge summary notification sent to the patient or referring physician includes excessive protected health information (PHI) in email subject lines, push notification previews, or unencrypted attachment metadata, exposing sensitive medical details to unauthorized observers.
Mitigations for T15:
•	M19: PHI Minimization in Notifications Mitigation Category: Data Protection Description: Discharge notifications contain only a generic alert ("Your discharge summary is ready") with a secure link to the full document behind authentication. No PHI appears in email subjects, preview text, push notification bodies, or URL parameters.
________________________________________
Data Stores
DS1: Electronic Health Records Database Description: The central clinical database storing comprehensive patient medical records including demographics, medical histories, diagnoses (ICD-10 codes), treatment plans, medication orders, lab and imaging results, surgical notes, and provider assignments. HIPAA-regulated with strict access controls and encryption requirements. Trust Boundary: Resides inside the Internal Clinical Network.
Susceptible Threats:
T16: EHR Database Record Tampering Threat Category: Tampering Risk Level: Critical Likelihood: Low Severity: Critical Score: 8.6 Description: An attacker or malicious insider with database-level access modifies clinical records directly in the EHR database, bypassing application-level controls and audit logging, to alter diagnoses, delete adverse event records, or fabricate treatment histories.
Mitigations for T16:
•	M14: Clinical Record Versioning with Change Tracking Mitigation Category: Data Protection Description: Every modification to a clinical record creates a new version with the previous version preserved immutably. Each change is tagged with the authenticated clinician's identity, timestamp, workstation ID, and a mandatory change reason field, enabling full reconstruction of the record's history.
•	M20: Database-Level Transparent Data Encryption and Access Auditing Mitigation Category: Data Protection Description: The EHR database employs transparent data encryption (TDE) for all data at rest and maintains a database-level audit log capturing every read, write, and schema change operation with the authenticated principal, independent of the application layer.
T17: Unauthorized EHR Data Disclosure Threat Category: Information Disclosure Risk Level: Critical Likelihood: Medium Severity: Critical Score: 9.0 Description: An attacker gains unauthorized read access to the EHR database, exfiltrating patient medical records, diagnoses, medications, and personal identifiers — constituting a HIPAA breach with regulatory penalties, legal liability, and severe patient harm.
Mitigations for T17:
•	M21: EHR Field-Level Encryption and Tokenization Mitigation Category: Data Protection Description: Sensitive EHR fields (SSN, diagnosis codes, medication lists) are encrypted at the field level using AES-256 with per-patient keys. Patient identifiers in non-clinical tables are tokenized, limiting the value of exfiltrated data even if database-level access is compromised.
•	M17: Data Loss Prevention and Anomalous Query Detection Mitigation Category: Data Protection Description: A data loss prevention layer monitors all data egress from the clinical records process, detecting and blocking bulk data extraction attempts, unusually large result sets, and query patterns inconsistent with normal clinical workflows.
T18: EHR Database Denial of Service Threat Category: Denial of Service Risk Level: High Likelihood: Medium Severity: High Score: 7.0 Description: An attacker or misconfigured process overwhelms the EHR database with excessive queries, long-running transactions, or lock contention, degrading database performance and preventing clinicians from accessing patient records during critical care situations.
Mitigations for T18:
•	M22: Database Connection Pooling and Query Throttling Mitigation Category: Availability & Resilience Description: The EHR database enforces per-service connection pool limits, query timeout thresholds, and automatic termination of runaway queries. Resource-intensive analytical queries are routed to a read replica, preserving the primary database's capacity for real-time clinical operations.
________________________________________
DS2: Insurance Claims Repository Description: Stores insurance eligibility verification records, pre-authorization codes, coverage details, co-payment amounts, claim submission statuses, and billing reconciliation data. Used by the insurance verification process and downstream billing systems. Trust Boundary: Resides inside the Internal Clinical Network.
Susceptible Threats:
T19: Insurance Claims Data Tampering Threat Category: Tampering Risk Level: High Likelihood: Low Severity: High Score: 6.8 Description: An attacker or malicious insider modifies insurance claim records — altering coverage amounts, pre-authorization codes, or billing codes — to commit insurance fraud, inflate reimbursements, or conceal denied claims.
Mitigations for T19:
•	M23: Claims Record Integrity Hashing Mitigation Category: Data Protection Description: Each insurance claims record includes a cryptographic hash of its key fields (policy number, authorization code, coverage amount, billing code) computed at creation and verified on every read, enabling detection of unauthorized modifications.
T20: Insurance Data Unauthorized Disclosure Threat Category: Information Disclosure Risk Level: Medium Likelihood: Medium Severity: Medium Score: 5.8 Description: An unauthorized user gains access to the insurance claims repository, exposing patient insurance policy numbers, coverage details, claims history, and billing information that could be used for insurance fraud or patient profiling.
Mitigations for T20:
•	M24: Insurance Data Role-Based Access Control Mitigation Category: Access Control Description: Access to the insurance claims repository is restricted to authorized billing staff and the insurance verification service account. Clinical staff cannot access insurance details unless they hold a specific billing role. All access is logged and audited weekly.
________________________________________
DS3: Clinical Audit Trail Description: An append-only audit log capturing all clinical system events — patient record access, modifications, referral submissions, insurance verifications, discharge summary generations, and authentication events. Required for HIPAA compliance and forensic investigation. Trust Boundary: Resides inside the Internal Clinical Network.
Susceptible Threats:
T21: Audit Trail Tampering Threat Category: Tampering Risk Level: High Likelihood: Low Severity: Critical Score: 7.8 Description: An attacker or malicious insider with elevated privileges modifies or deletes audit log entries to cover traces of unauthorized clinical record access, data exfiltration, or fraudulent insurance claims, undermining the integrity of the compliance record.
Mitigations for T21:
•	M25: WORM Storage for Audit Logs Mitigation Category: Logging & Monitoring Description: The clinical audit trail is stored on a WORM (Write Once Read Many) storage backend with cryptographic chaining (hash-linked entries), ensuring that no entry can be modified or deleted after creation, even by database administrators or system operators.
T22: Audit Log Repudiation Threat Category: Repudiation Risk Level: Medium Likelihood: Low Severity: High Score: 5.6 Description: An actor disputes that an event recorded in the audit trail actually occurred or claims the log entry was fabricated, and the system lacks cryptographic proof of log entry authenticity and temporal ordering.
Mitigations for T22:
•	M26: Cryptographically Signed Audit Entries with Timestamping Mitigation Category: Logging & Monitoring Description: Each audit log entry is individually signed using the system's HSM-backed signing key and includes a trusted timestamp from an RFC 3161 timestamping authority, providing non-repudiable proof of both the entry's content and the time it was recorded.
T23: Audit Log Denial of Service Threat Category: Denial of Service Risk Level: Medium Likelihood: Medium Severity: Medium Score: 5.2 Description: An attacker generates an excessive volume of auditable events to overwhelm the audit log storage or processing capacity, causing legitimate audit entries to be dropped, delayed, or the audit system to become unavailable.
Mitigations for T23:
•	M27: Audit Log Buffering and Overflow Protection Mitigation Category: Availability & Resilience Description: The audit logging pipeline uses an asynchronous message queue with guaranteed delivery, automatic disk-based overflow buffering, and alerting when throughput exceeds 80% of capacity. Clinical operations are never blocked by audit log backpressure.
________________________________________
Data Flows
DF1: Patient Registration Submission Name: Patient Registration Submission Description: The patient submits demographic data, identification documents, and insurance details through the patient portal to the Patient Registration Gateway. Protocol: HTTPS Crosses Trust Boundaries: Yes — from outside into Hospital Perimeter Network (DMZ) (TB1). From: EE1 (Patient) → P1 (Patient Registration Gateway)
DF2: Duplicate Record Check Name: Duplicate Record Check Description: The Patient Registration Gateway queries the EHR Database to check for existing patient records with matching demographics to prevent duplicate registrations. Protocol: TLS Crosses Trust Boundaries: Yes — from Hospital Perimeter Network (DMZ) (TB1) into Internal Clinical Network (TB2). From: P1 (Patient Registration Gateway) → DS1 (EHR Database)
DF3: Insurance Verification Request Name: Insurance Verification Request Description: The Patient Registration Gateway forwards the patient's insurance policy details to the Verify Insurance Eligibility process for coverage verification. Protocol: HTTPS Crosses Trust Boundaries: No — both reside within the Hospital Perimeter Network (DMZ) (TB1). From: P1 (Patient Registration Gateway) → P2 (Verify Insurance Eligibility)
DF4: Insurance Eligibility Query Name: Insurance Eligibility Query Description: The Verify Insurance Eligibility process sends an HL7 FHIR eligibility request to the external Insurance Provider. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Hospital Perimeter Network (DMZ) (TB1) to outside. From: P2 (Verify Insurance Eligibility) → EE3 (Insurance Provider)
DF5: Insurance Eligibility Response Name: Insurance Eligibility Response Description: The Insurance Provider returns coverage details, co-payment amounts, and pre-authorization codes to the Verify Insurance Eligibility process. Protocol: HTTPS Crosses Trust Boundaries: Yes — from outside into Hospital Perimeter Network (DMZ) (TB1). From: EE3 (Insurance Provider) → P2 (Verify Insurance Eligibility)
DF6: Insurance Verification Result Storage Name: Insurance Verification Result Storage Description: The Verify Insurance Eligibility process writes the verified insurance status, coverage details, and pre-authorization codes to the Insurance Claims Repository. Protocol: TLS Crosses Trust Boundaries: Yes — from Hospital Perimeter Network (DMZ) (TB1) into Internal Clinical Network (TB2). From: P2 (Verify Insurance Eligibility) → DS2 (Insurance Claims Repository)
DF7: Physician Referral Submission Name: Physician Referral Submission Description: The referring physician submits a referral letter with clinical notes and admission request through the physician referral API. Protocol: HTTPS (with mutual TLS) Crosses Trust Boundaries: Yes — from outside into Hospital Perimeter Network (DMZ) (TB1). From: EE2 (Referring Physician) → P1 (Patient Registration Gateway)
DF8: Clinical Record Access Name: Clinical Record Access Description: The Manage Clinical Records process reads and writes clinical data (admission notes, diagnoses, treatment plans, medications, lab results) to and from the EHR Database. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Clinical Network (TB2). From: P3 (Manage Clinical Records) ↔ DS1 (EHR Database)
DF9: Discharge Summary Data Retrieval Name: Discharge Summary Data Retrieval Description: The Generate Discharge Summary process reads the patient's complete admission record, treatment history, and medication list from the EHR Database to compile the discharge summary. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Clinical Network (TB2). From: P4 (Generate Discharge Summary) → DS1 (EHR Database)
DF10: Discharge Summary to Patient Name: Discharge Summary to Patient Description: The Generate Discharge Summary process sends a notification with a secure link to the discharge summary to the patient via the patient portal. Protocol: HTTPS Crosses Trust Boundaries: Yes — from Internal Clinical Network (TB2) through Hospital Perimeter Network (DMZ) (TB1) to outside. From: P4 (Generate Discharge Summary) → EE1 (Patient)
DF11: Discharge Summary to Referring Physician Name: Discharge Summary to Referring Physician Description: The Generate Discharge Summary process transmits the signed discharge summary to the referring physician via the physician referral API. Protocol: HTTPS (with mutual TLS) Crosses Trust Boundaries: Yes — from Internal Clinical Network (TB2) through Hospital Perimeter Network (DMZ) (TB1) to outside. From: P4 (Generate Discharge Summary) → EE2 (Referring Physician)
DF12: Clinical Audit Log Entry Name: Clinical Audit Log Entry Description: The Manage Clinical Records process writes audit events (record access, modifications, authorization checks) to the Clinical Audit Trail. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Internal Clinical Network (TB2). From: P3 (Manage Clinical Records) → DS3 (Clinical Audit Trail)
DF13: Registration Audit Log Entry Name: Registration Audit Log Entry Description: The Patient Registration Gateway writes audit events (registration attempts, duplicate checks, validation outcomes) to the Clinical Audit Trail. Protocol: TLS Crosses Trust Boundaries: Yes — from Hospital Perimeter Network (DMZ) (TB1) into Internal Clinical Network (TB2). From: P1 (Patient Registration Gateway) → DS3 (Clinical Audit Trail)
________________________________________
2. Threat Modeling Diagram: Patient Admission & Medical Records Threats
Diagram Name: TM_PatientAdmissionRecords
This threat modeling diagram captures the threats and mitigations associated with the DFD_PatientAdmissionRecords diagram. Each threat belongs to a STRIDE threat category and is linked to mitigations from the corresponding mitigation categories.
Threats
T1: Patient Identity Spoofing — Threat Category: Spoofing | Risk Level: Critical | Likelihood: High | Severity: Critical | Score: 8.5
T2: Patient Action Repudiation — Threat Category: Repudiation | Risk Level: Medium | Likelihood: Medium | Severity: Medium | Score: 5.0
T3: Physician Identity Spoofing — Threat Category: Spoofing | Risk Level: High | Likelihood: Medium | Severity: High | Score: 7.2
T4: Insurance Provider Spoofing — Threat Category: Spoofing | Risk Level: High | Likelihood: Low | Severity: High | Score: 6.4
T5: Insurance Communication Repudiation — Threat Category: Repudiation | Risk Level: Medium | Likelihood: Medium | Severity: Medium | Score: 5.5
T6: Registration Data Tampering — Threat Category: Tampering | Risk Level: High | Likelihood: Medium | Severity: High | Score: 7.0
T7: Patient Record Information Disclosure — Threat Category: Information Disclosure | Risk Level: Critical | Likelihood: Medium | Severity: Critical | Score: 8.8
T8: Registration Service Denial of Service — Threat Category: Denial of Service | Risk Level: Medium | Likelihood: High | Severity: Medium | Score: 6.0
T9: Insurance Data Tampering in Transit — Threat Category: Tampering | Risk Level: High | Likelihood: Medium | Severity: High | Score: 7.4
T10: Eligibility Process Elevation of Privilege — Threat Category: Elevation of Privilege | Risk Level: High | Likelihood: Low | Severity: Critical | Score: 7.8
T11: Unauthorized Clinical Record Modification — Threat Category: Tampering | Risk Level: Critical | Likelihood: Medium | Severity: Critical | Score: 9.0
T12: Clinical Record Access Repudiation — Threat Category: Repudiation | Risk Level: Medium | Likelihood: Medium | Severity: High | Score: 6.2
T13: Patient Data Exfiltration — Threat Category: Information Disclosure | Risk Level: Critical | Likelihood: Medium | Severity: Critical | Score: 9.2
T14: Discharge Summary Tampering — Threat Category: Tampering | Risk Level: High | Likelihood: Low | Severity: High | Score: 6.8
T15: PHI Exposure in Discharge Notifications — Threat Category: Information Disclosure | Risk Level: High | Likelihood: Medium | Severity: High | Score: 7.5
T16: EHR Database Record Tampering — Threat Category: Tampering | Risk Level: Critical | Likelihood: Low | Severity: Critical | Score: 8.6
T17: Unauthorized EHR Data Disclosure — Threat Category: Information Disclosure | Risk Level: Critical | Likelihood: Medium | Severity: Critical | Score: 9.0
T18: EHR Database Denial of Service — Threat Category: Denial of Service | Risk Level: High | Likelihood: Medium | Severity: High | Score: 7.0
T19: Insurance Claims Data Tampering — Threat Category: Tampering | Risk Level: High | Likelihood: Low | Severity: High | Score: 6.8
T20: Insurance Data Unauthorized Disclosure — Threat Category: Information Disclosure | Risk Level: Medium | Likelihood: Medium | Severity: Medium | Score: 5.8
T21: Audit Trail Tampering — Threat Category: Tampering | Risk Level: High | Likelihood: Low | Severity: Critical | Score: 7.8
T22: Audit Log Repudiation — Threat Category: Repudiation | Risk Level: Medium | Likelihood: Low | Severity: High | Score: 5.6
T23: Audit Log Denial of Service — Threat Category: Denial of Service | Risk Level: Medium | Likelihood: Medium | Severity: Medium | Score: 5.2
Mitigations
M1: Multi-Factor Patient Authentication — Mitigation Category: Authentication & Identity M2: Biometric Identity Verification at Registration — Mitigation Category: Authentication & Identity M3: Patient Action Audit Trail with Digital Signatures — Mitigation Category: Logging & Monitoring M4: Physician Mutual TLS and Certificate Authentication — Mitigation Category: Authentication & Identity M5: Physician API Key Rotation and Scope Restriction — Mitigation Category: Access Control M6: Insurance API Endpoint Certificate Pinning — Mitigation Category: Network Security M7: Insurance Transaction Logging with Message Signing — Mitigation Category: Logging & Monitoring M8: Server-Side Registration Data Validation — Mitigation Category: Input Validation M9: End-to-End Encryption for Registration Payloads — Mitigation Category: Network Security M10: Structured Error Responses without PII Leakage — Mitigation Category: Data Protection M11: Registration Endpoint Rate Limiting and WAF Rules — Mitigation Category: Availability & Resilience M12: FHIR Message Integrity Validation — Mitigation Category: Input Validation M13: DMZ Service Account Isolation and Least Privilege — Mitigation Category: Access Control M14: Clinical Record Versioning with Change Tracking — Mitigation Category: Data Protection M15: Dual Authorization for Critical Record Changes — Mitigation Category: Access Control M16: Break-the-Glass Access Logging — Mitigation Category: Logging & Monitoring M17: Data Loss Prevention and Anomalous Query Detection — Mitigation Category: Data Protection M18: Discharge Summary Digital Signing — Mitigation Category: Data Protection M19: PHI Minimization in Notifications — Mitigation Category: Data Protection M20: Database-Level Transparent Data Encryption and Access Auditing — Mitigation Category: Data Protection M21: EHR Field-Level Encryption and Tokenization — Mitigation Category: Data Protection M22: Database Connection Pooling and Query Throttling — Mitigation Category: Availability & Resilience M23: Claims Record Integrity Hashing — Mitigation Category: Data Protection M24: Insurance Data Role-Based Access Control — Mitigation Category: Access Control M25: WORM Storage for Audit Logs — Mitigation Category: Logging & Monitoring M26: Cryptographically Signed Audit Entries with Timestamping — Mitigation Category: Logging & Monitoring M27: Audit Log Buffering and Overflow Protection — Mitigation Category: Availability & Resilience
Threat-to-Mitigation Mapping — Case 1
T1: Patient Identity Spoofing → M1, M2 T2: Patient Action Repudiation → M3 T3: Physician Identity Spoofing → M4, M5 T4: Insurance Provider Spoofing → M6 T5: Insurance Communication Repudiation → M7 T6: Registration Data Tampering → M8, M9 T7: Patient Record Information Disclosure → M10 T8: Registration Service Denial of Service → M11 T9: Insurance Data Tampering in Transit → M12 T10: Eligibility Process Elevation of Privilege → M13 T11: Unauthorized Clinical Record Modification → M14, M15 T12: Clinical Record Access Repudiation → M16 T13: Patient Data Exfiltration → M17 T14: Discharge Summary Tampering → M18 T15: PHI Exposure in Discharge Notifications → M19 T16: EHR Database Record Tampering → M14, M20 T17: Unauthorized EHR Data Disclosure → M21, M17 
T18: EHR Database Denial of Service → M22 
T19: Insurance Claims Data Tampering → M23 
T20: Insurance Data Unauthorized Disclosure → M24 
T21: Audit Trail Tampering → M25 
T22: Audit Log Repudiation → M26 
T23: Audit Log Denial of Service → M27
________________________________________
3. Threat/Mitigation Categorization Diagram
Diagram Name: CAT_ThreatMitigationCategorizationMedical
This diagram defines the threat categories and mitigation categories used across the threat modeling diagrams. Below are the categories introduced in Case 1 (additional categories may be introduced in Case 2).
Threat Categories
Spoofing Description: Threats involving an attacker impersonating another user, system, or service to gain unauthorized access or perform unauthorized actions. In the STRIDE model, spoofing relates to violations of authentication mechanisms.
Tampering Description: Threats involving unauthorized modification of data in transit or at rest, including alteration of messages, records, or configuration to subvert system integrity.
Repudiation Description: Threats where an actor denies having performed an action and the system lacks sufficient evidence (logs, signatures, timestamps) to prove otherwise.
Information Disclosure Description: Threats involving the exposure of sensitive or confidential information to unauthorized parties, whether through direct access, side channels, or inadequate output sanitization.
Denial of Service Description: Threats aimed at degrading or disabling system availability by overwhelming resources, exploiting resource exhaustion vulnerabilities, or disrupting dependent services.
Elevation of Privilege Description: Threats where an attacker gains access rights beyond what was originally granted, allowing them to perform administrative or restricted operations without proper authorization.
Mitigation Categories
Authentication & Identity Description: Mitigations that verify the identity of users, services, or systems before granting access. Includes multi-factor authentication, mutual TLS, biometric verification, certificate validation, and identity federation.
Network Security Description: Mitigations that protect data in transit and enforce secure communication channels. Includes TLS enforcement, certificate pinning, end-to-end encryption, network segmentation, and firewall rules.
Input Validation Description: Mitigations that validate, sanitize, and verify the integrity of all incoming data before processing. Includes format checks, schema validation, digital signature verification, and message integrity validation.
Availability & Resilience Description: Mitigations that maintain system availability under adverse conditions. Includes rate limiting, connection pooling, query throttling, WAF rules, overflow protection, and capacity planning.
Logging & Monitoring Description: Mitigations that provide audit trails, event logging, and real-time monitoring for detection, forensics, and non-repudiation. Includes immutable logs, WORM storage, cryptographic timestamping, and break-the-glass logging.
Data Protection Description: Mitigations that protect data confidentiality and integrity at rest and in output. Includes encryption (field-level, TDE), data masking, tokenization, versioning, change tracking, integrity hashing, DLP, and digital signing.
Access Control Description: Mitigations that enforce authorization policies and least-privilege principles. Includes role-based access control, service account isolation, dual authorization, API scope restrictions, and key rotation.






Case 2/2 — Pharmacy Prescription & Medication Dispensing
Domain: MedTrack General Hospital — the same regional hospital from Case 1. This case covers the hospital's outpatient pharmacy system, which receives electronic prescriptions from attending physicians, verifies drug interactions and patient allergies against the EHR, processes medication dispensing, and communicates with the national drug registry for controlled substance tracking.
________________________________________
1. DFD Diagram: Pharmacy Prescription & Medication Dispensing
Diagram Name: DFD_PharmacyPrescriptionDispensing
This Data Flow Diagram models how prescription data flows from the prescribing physician through verification, dispensing, and controlled substance reporting — including interactions with the hospital's existing EHR database and an external national drug registry.
________________________________________
Trust Boundaries
TB3: Pharmacy Application Zone Description: The secured zone enclosing the pharmacy's prescription processing services, drug interaction checker, dispensing management system, and the local pharmacy inventory database. Protected by application-level authentication, role-based access enforcement, and dedicated firewall rules isolating pharmacy systems from the broader hospital network.
TB4: Hospital Clinical Data Zone Description: The zone enclosing the hospital's shared clinical data assets — specifically the Electronic Health Records (EHR) Database and the Clinical Audit Trail — that are accessed by the pharmacy system for patient allergy and medication history lookups. This is the same internal clinical infrastructure referenced in Case 1, now accessed cross-zone by pharmacy services.
________________________________________
External Entities
EE4: Prescribing Physician Description: An attending physician within MedTrack General Hospital who creates and submits electronic prescriptions (e-prescriptions) through the hospital's clinical workstation. Each prescription includes patient identifier, medication name, dosage, route, frequency, quantity, and the physician's digital signature. Trust Boundary: Resides outside both trust boundaries — on the hospital's general clinical workstation network.
Susceptible Threats:
T24: Prescriber Identity Spoofing Threat Category: Spoofing Risk Level: Critical Likelihood: Medium Severity: Critical Score: 8.9 Description: An attacker impersonates a licensed physician by using stolen credentials, a compromised workstation, or a forged digital signature to submit fraudulent prescriptions — particularly for controlled substances — enabling drug diversion, patient harm, or regulatory violations.
Mitigations for T24:
•	M28: Prescriber Digital Signature Verification Mitigation Category: Authentication & Identity Description: Every e-prescription must carry a valid digital signature from the prescribing physician's hospital-issued PKI certificate. The pharmacy system verifies the signature against the hospital's certificate authority and confirms the physician's active medical license status before accepting any prescription.
T25: Prescription Submission Repudiation Threat Category: Repudiation Risk Level: Medium Likelihood: Medium Severity: Medium Score: 5.4 Description: A physician denies having prescribed a specific medication or dosage, and the system lacks sufficient non-repudiable evidence linking the prescription to the physician's authenticated session, workstation, and digital signature at the time of submission.
Mitigations for T25:
•	M29: Prescription Submission Immutable Logging Mitigation Category: Logging & Monitoring Description: Every prescription submission is logged with the physician's authenticated identity, digital signature hash, workstation ID, timestamp, and the complete prescription content, stored on an append-only ledger that cannot be modified or deleted after creation.
________________________________________
EE5: National Drug Registry (NDR) Description: A government-operated controlled substance monitoring database that tracks the prescribing and dispensing of scheduled medications (opioids, benzodiazepines, stimulants) across all pharmacies and hospitals in the country. MedTrack is legally required to report every controlled substance dispensing event to the NDR within 24 hours. Trust Boundary: Resides outside both trust boundaries — on the external government network.
Susceptible Threats:
T26: Drug Registry Endpoint Spoofing Threat Category: Spoofing Risk Level: High Likelihood: Low Severity: High Score: 6.6 Description: An attacker impersonates the National Drug Registry's API endpoint through DNS poisoning or certificate forgery, intercepting controlled substance reports to suppress reporting of suspicious prescriptions or to harvest controlled substance dispensing data across the hospital.
Mitigations for T26:
•	M30: NDR API Mutual TLS with Certificate Pinning Mitigation Category: Network Security Description: All communication with the National Drug Registry uses mutual TLS authentication with the NDR's certificate fingerprint pinned in the pharmacy system's configuration. Both sides verify each other's identity before any data exchange, and certificate changes require manual administrative approval.
________________________________________
Processes
P5: Receive and Validate Prescription Description: Receives incoming e-prescriptions from prescribing physicians, validates the prescription format (medication code, dosage range, quantity limits), verifies the prescriber's digital signature, and checks the prescription against formulary rules. Valid prescriptions are queued for drug interaction checking. Trust Boundary: Resides inside the Pharmacy Application Zone (TB3).
Susceptible Threats:
T27: Prescription Data Tampering Threat Category: Tampering Risk Level: Critical Likelihood: Medium Severity: Critical Score: 8.5 Description: An attacker intercepts and modifies an e-prescription in transit between the physician's workstation and the pharmacy system, altering the medication, dosage, or quantity — potentially substituting a controlled substance or increasing a dosage to dangerous levels, directly endangering patient safety.
Mitigations for T27:
•	M31: Prescription Payload Integrity Verification Mitigation Category: Input Validation Description: Each e-prescription payload includes a HMAC-SHA256 integrity hash computed over the full prescription content using a shared secret between the prescribing workstation and the pharmacy system. The receiving process recomputes and compares the hash before accepting the prescription.
•	M28: Prescriber Digital Signature Verification Mitigation Category: Authentication & Identity Description: Every e-prescription must carry a valid digital signature from the prescribing physician's hospital-issued PKI certificate, ensuring that any post-signature modification is detectable.
T28: Prescription Validation Bypass via Privilege Escalation Threat Category: Elevation of Privilege Risk Level: High Likelihood: Low Severity: Critical Score: 7.6 Description: An attacker exploits a flaw in the prescription validation process to escalate from a limited pharmacy technician role to an override-capable pharmacist role, allowing them to approve prescriptions that would normally be flagged for dosage violations, formulary restrictions, or missing prescriber credentials.
Mitigations for T28:
•	M32: Role-Based Prescription Approval Enforcement Mitigation Category: Access Control Description: Prescription approval and override actions are restricted to authenticated pharmacist-role accounts. The system enforces server-side role checks at every approval step and rejects override attempts from technician-level sessions regardless of client-side UI state.
________________________________________
P6: Check Drug Interactions Description: Queries the EHR Database for the patient's current medication list, known allergies, and clinical conditions, then cross-references the new prescription against a drug interaction knowledge base. Returns one of three outcomes: clear, warning (non-critical interaction), or block (contraindicated combination requiring pharmacist override). Trust Boundary: Resides inside the Pharmacy Application Zone (TB3).
Susceptible Threats:
T29: Drug Interaction Data Disclosure Threat Category: Information Disclosure Risk Level: High Likelihood: Medium Severity: High Score: 7.2 Description: The drug interaction checking process retrieves the patient's full medication history and allergy profile from the EHR but inadvertently exposes this data through verbose API responses, debug logging, or insufficiently scoped queries — revealing sensitive medical details beyond what the pharmacy workflow requires.
Mitigations for T29:
•	M33: Minimum Necessary Data Retrieval from EHR Mitigation Category: Data Protection Description: The drug interaction query to the EHR is scoped to return only the patient's active medications and documented allergies. Diagnosis codes, treatment plans, physician notes, and other clinical details are explicitly excluded from the query projection, enforcing the HIPAA minimum necessary standard.
________________________________________
P7: Dispense Medication Description: Manages the physical dispensing workflow — confirms the pharmacist's approval, deducts the dispensed quantity from the pharmacy inventory, prints the medication label with patient instructions, and updates the dispensing record. For controlled substances, triggers a report to the National Drug Registry. Trust Boundary: Resides inside the Pharmacy Application Zone (TB3).
Susceptible Threats:
T30: Dispensing Record Tampering Threat Category: Tampering Risk Level: High Likelihood: Low Severity: High Score: 7.0 Description: An attacker or malicious pharmacy staff member modifies dispensing records after the fact — altering quantities dispensed, removing entries for controlled substances, or falsifying timestamps — to conceal drug diversion or inventory discrepancies.
Mitigations for T30:
•	M34: Dispensing Record Cryptographic Sealing Mitigation Category: Data Protection Description: Each dispensing record is sealed with a cryptographic hash of its key fields (prescription ID, medication code, quantity, patient ID, timestamp, dispensing pharmacist). The hash is stored separately and verified on every read, enabling immediate detection of any post-creation modification.
T31: Controlled Substance Reporting Denial of Service Threat Category: Denial of Service Risk Level: Medium Likelihood: Medium Severity: Medium Score: 5.8 Description: An attacker disrupts the reporting channel to the National Drug Registry by flooding the outbound queue or exploiting connection timeouts, causing controlled substance reports to be delayed beyond the 24-hour regulatory deadline, exposing the hospital to compliance penalties.
Mitigations for T31:
•	M35: Resilient Reporting Queue with Guaranteed Delivery Mitigation Category: Availability & Resilience Description: Controlled substance reports are placed in a persistent message queue with guaranteed delivery, automatic retry with exponential backoff, and disk-based overflow buffering. If the NDR is unreachable for more than 4 hours, an alert is escalated to the pharmacy compliance officer.
________________________________________
Data Stores
DS1: Electronic Health Records (EHR) Database Description: The same central clinical database from Case 1, storing patient demographics, medical histories, medication lists, allergies, diagnoses, and treatment plans. The pharmacy system queries this database (read-only) for drug interaction checks and patient allergy verification. Trust Boundary: Resides inside the Hospital Clinical Data Zone (TB4).
Susceptible Threats:
T32: Unauthorized Patient Medication History Disclosure Threat Category: Information Disclosure Risk Level: Critical Likelihood: Medium Severity: Critical Score: 8.4 Description: An attacker exploits the pharmacy system's read access to the EHR to extract patient medication histories, allergy profiles, and associated diagnoses beyond the scope of the current prescription, enabling patient profiling, blackmail, or a HIPAA breach notification obligation.
Mitigations for T32:
•	M33: Minimum Necessary Data Retrieval from EHR Mitigation Category: Data Protection Description: The drug interaction query to the EHR is scoped to return only the patient's active medications and documented allergies, enforcing the HIPAA minimum necessary standard.
•	M36: Cross-Zone Query Monitoring and Alerting Mitigation Category: Logging & Monitoring Description: All queries from the Pharmacy Application Zone to the EHR Database are logged with the requesting service identity, patient ID queried, fields returned, and timestamp. Anomalous query patterns (bulk lookups, out-of-hours access, high-frequency single-patient queries) trigger real-time alerts to the security operations team.
T33: EHR Medication Data Tampering via Pharmacy Channel Threat Category: Tampering Risk Level: High Likelihood: Low Severity: Critical Score: 7.8 Description: An attacker exploits a misconfigured pharmacy-to-EHR integration to write data to the EHR database through what should be a read-only channel, modifying patient allergy records or medication lists to suppress drug interaction warnings for future prescriptions.
Mitigations for T33:
•	M37: Read-Only Database Role for Pharmacy Services Mitigation Category: Access Control Description: The pharmacy system's EHR database service account is provisioned with strictly read-only permissions on a dedicated read replica. The account has no write, update, or delete privileges on any EHR table, and the read replica enforces this at the database engine level independently of application logic.
________________________________________
DS4: Pharmacy Dispensing & Inventory Records Description: Stores all prescription processing records (received, validated, approved, dispensed, rejected), dispensing events (medication, quantity, dispensing pharmacist, timestamp), pharmacy inventory levels, and controlled substance tracking data. Trust Boundary: Resides inside the Pharmacy Application Zone (TB3).
Susceptible Threats:
T34: Controlled Substance Dispensing Record Deletion Threat Category: Tampering Risk Level: Critical Likelihood: Low Severity: Critical Score: 8.2 Description: A malicious insider deletes or modifies controlled substance dispensing records to conceal drug diversion — removing entries that would otherwise be reconciled against physical inventory counts and reported to the National Drug Registry during audits.
Mitigations for T34:
•	M34: Dispensing Record Cryptographic Sealing Mitigation Category: Data Protection Description: Each dispensing record is sealed with a cryptographic hash of its key fields, enabling immediate detection of any post-creation modification or deletion attempt.
•	M38: Append-Only Controlled Substance Ledger Mitigation Category: Logging & Monitoring Description: All controlled substance dispensing events are additionally written to a dedicated append-only ledger on WORM storage, separate from the main dispensing records. This ledger cannot be modified or deleted even by database administrators, providing a tamper-proof audit trail for regulatory inspections.
________________________________________
DS3: Clinical Audit Trail Description: The same append-only audit log from Case 1, capturing all clinical and pharmacy system events — prescription submissions, drug interaction checks, dispensing events, controlled substance reports, and authentication activities. Required for HIPAA compliance and DEA controlled substance auditing. Trust Boundary: Resides inside the Hospital Clinical Data Zone (TB4).
Susceptible Threats:
T35: Pharmacy Audit Trail Denial of Service Threat Category: Denial of Service Risk Level: Medium Likelihood: Medium Severity: High Score: 5.6 Description: An attacker or misconfigured process generates an excessive volume of pharmacy-related audit events, saturating the Clinical Audit Trail's ingestion capacity and causing legitimate audit entries (particularly controlled substance tracking events) to be delayed or dropped, creating compliance gaps.
Mitigations for T35:
•	M39: Audit Pipeline Priority Queuing and Backpressure Protection Mitigation Category: Availability & Resilience Description: The audit logging pipeline assigns higher priority to controlled substance events over routine prescription events. Backpressure from audit log saturation triggers throttling of lower-priority events rather than dropping high-priority ones, and capacity alerts are raised when throughput exceeds 70% of maximum.
________________________________________
Data Flows
DF16: E-Prescription Submission Name: E-Prescription Submission Description: The prescribing physician submits a digitally signed e-prescription (medication, dosage, quantity, patient ID, physician signature) to the Receive and Validate Prescription process. Protocol: HTTPS Crosses Trust Boundaries: Yes — from outside into Pharmacy Application Zone (TB3). From: EE4 (Prescribing Physician) → P5 (Receive and Validate Prescription)
DF17: Patient Allergy and Medication Query Name: Patient Allergy and Medication Query Description: The Check Drug Interactions process queries the EHR Database for the patient's active medication list, documented allergies, and relevant clinical conditions. Protocol: TLS Crosses Trust Boundaries: Yes — from Pharmacy Application Zone (TB3) into Hospital Clinical Data Zone (TB4). From: P6 (Check Drug Interactions) → DS1 (EHR Database)
DF18: Allergy and Medication Response Name: Allergy and Medication Response Description: The EHR Database returns the patient's active medications, allergy list, and relevant clinical flags to the Check Drug Interactions process. Protocol: TLS Crosses Trust Boundaries: Yes — from Hospital Clinical Data Zone (TB4) into Pharmacy Application Zone (TB3). From: DS1 (EHR Database) → P6 (Check Drug Interactions)
DF19: Validated Prescription Handoff Name: Validated Prescription Handoff Description: The validated prescription (confirmed prescriber identity, format-compliant, formulary-checked) is forwarded from the Receive and Validate Prescription process to the Check Drug Interactions process. Protocol: HTTPS Crosses Trust Boundaries: No — both reside within the Pharmacy Application Zone (TB3). From: P5 (Receive and Validate Prescription) → P6 (Check Drug Interactions)
DF20: Interaction-Cleared Prescription Name: Interaction-Cleared Prescription Description: The drug interaction-cleared prescription (or a prescription with pharmacist-overridden warnings) is forwarded from the Check Drug Interactions process to the Dispense Medication process. Protocol: HTTPS Crosses Trust Boundaries: No — both reside within the Pharmacy Application Zone (TB3). From: P6 (Check Drug Interactions) → P7 (Dispense Medication)
DF21: Dispensing Record Storage Name: Dispensing Record Storage Description: The Dispense Medication process writes the completed dispensing record (medication, quantity, patient, pharmacist, timestamp, cryptographic seal) to the Pharmacy Dispensing & Inventory Records. Protocol: TLS Crosses Trust Boundaries: No — both reside within the Pharmacy Application Zone (TB3). From: P7 (Dispense Medication) → DS4 (Pharmacy Dispensing & Inventory Records)
DF22: Controlled Substance Report Name: Controlled Substance Report Description: The Dispense Medication process transmits a controlled substance dispensing report to the National Drug Registry, containing the medication schedule, quantity, patient identifier (anonymized), prescriber license number, and dispensing timestamp. Protocol: HTTPS (with mutual TLS) Crosses Trust Boundaries: Yes — from Pharmacy Application Zone (TB3) to outside. From: P7 (Dispense Medication) → EE5 (National Drug Registry / NDR)
DF23: Prescription Processing Audit Entry Name: Prescription Processing Audit Entry Description: The Receive and Validate Prescription process writes an audit record for every prescription received — capturing prescriber identity, signature verification result, validation outcome, and timestamp. Protocol: TLS Crosses Trust Boundaries: Yes — from Pharmacy Application Zone (TB3) into Hospital Clinical Data Zone (TB4). From: P5 (Receive and Validate Prescription) → DS3 (Clinical Audit Trail)
DF24: Dispensing Audit Entry Name: Dispensing Audit Entry Description: The Dispense Medication process writes an audit record for every dispensing event — capturing medication dispensed, quantity, patient, dispensing pharmacist, controlled substance flag, and NDR report status. Protocol: TLS Crosses Trust Boundaries: Yes — from Pharmacy Application Zone (TB3) into Hospital Clinical Data Zone (TB4). From: P7 (Dispense Medication) → DS3 (Clinical Audit Trail)
________________________________________
2. Threat Modeling Diagram: Pharmacy Prescription & Medication Dispensing Threats
Diagram Name: TM_PharmacyPrescriptionDispensing
This threat modeling diagram captures the threats and mitigations associated with the DFD_PharmacyPrescriptionDispensing diagram. Each threat belongs to a STRIDE threat category and is linked to mitigations from the corresponding mitigation categories.
Threats
T24: Prescriber Identity Spoofing — Threat Category: Spoofing | Risk Level: Critical | Likelihood: Medium | Severity: Critical | Score: 8.9
T25: Prescription Submission Repudiation — Threat Category: Repudiation | Risk Level: Medium | Likelihood: Medium | Severity: Medium | Score: 5.4
T26: Drug Registry Endpoint Spoofing — Threat Category: Spoofing | Risk Level: High | Likelihood: Low | Severity: High | Score: 6.6
T27: Prescription Data Tampering — Threat Category: Tampering | Risk Level: Critical | Likelihood: Medium | Severity: Critical | Score: 8.5
T28: Prescription Validation Bypass via Privilege Escalation — Threat Category: Elevation of Privilege | Risk Level: High | Likelihood: Low | Severity: Critical | Score: 7.6
T29: Drug Interaction Data Disclosure — Threat Category: Information Disclosure | Risk Level: High | Likelihood: Medium | Severity: High | Score: 7.2
T30: Dispensing Record Tampering — Threat Category: Tampering | Risk Level: High | Likelihood: Low | Severity: High | Score: 7.0
T31: Controlled Substance Reporting Denial of Service — Threat Category: Denial of Service | Risk Level: Medium | Likelihood: Medium | Severity: Medium | Score: 5.8
T32: Unauthorized Patient Medication History Disclosure — Threat Category: Information Disclosure | Risk Level: Critical | Likelihood: Medium | Severity: Critical | Score: 8.4
T33: EHR Medication Data Tampering via Pharmacy Channel — Threat Category: Tampering | Risk Level: High | Likelihood: Low | Severity: Critical | Score: 7.8
T34: Controlled Substance Dispensing Record Deletion — Threat Category: Tampering | Risk Level: Critical | Likelihood: Low | Severity: Critical | Score: 8.2
T35: Pharmacy Audit Trail Denial of Service — Threat Category: Denial of Service | Risk Level: Medium | Likelihood: Medium | Severity: High | Score: 5.6
Mitigations
M28: Prescriber Digital Signature Verification — Mitigation Category: Authentication & Identity 
M29: Prescription Submission Immutable Logging — Mitigation Category: Logging & Monitoring 
M30: NDR API Mutual TLS with Certificate Pinning — Mitigation Category: Network Security 
M31: Prescription Payload Integrity Verification — Mitigation Category: Input Validation 
M32: Role-Based Prescription Approval Enforcement — Mitigation Category: Access Control 
M33: Minimum Necessary Data Retrieval from EHR — Mitigation Category: Data Protection 
M34: Dispensing Record Cryptographic Sealing — Mitigation Category: Data Protection 
M35: Resilient Reporting Queue with Guaranteed Delivery — Mitigation Category: Availability & Resilience 
M36: Cross-Zone Query Monitoring and Alerting — Mitigation Category: Logging & Monitoring 
M37: Read-Only Database Role for Pharmacy Services — Mitigation Category: Access Control 
M38: Append-Only Controlled Substance Ledger — Mitigation Category: Logging & Monitoring 
M39: Audit Pipeline Priority Queuing and Backpressure Protection — Mitigation Category: Availability & Resilience
Threat-to-Mitigation Mapping — Case 2
T24: Prescriber Identity Spoofing → M28 
T25: Prescription Submission Repudiation → M29 
T26: Drug Registry Endpoint Spoofing → M30 
T27: Prescription Data Tampering → M31, M28 
T28: Prescription Validation Bypass via Privilege Escalation → M32 
T29: Drug Interaction Data Disclosure → M33 
T30: Dispensing Record Tampering → M34 
T31: Controlled Substance Reporting Denial of Service → M35 
T32: Unauthorized Patient Medication History Disclosure → M33, M36 
T33: EHR Medication Data Tampering via Pharmacy Channel → M37 
T34: Controlled Substance Dispensing Record Deletion → M34, M38 
T35: Pharmacy Audit Trail Denial of Service → M39"""