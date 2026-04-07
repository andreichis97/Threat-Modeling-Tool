questions_list = [
    # Category 1: Direct relation queries
    {"category_id": "1", "question_id": "1", "question": 'What is the risk level of "Carrier Identity Spoofing"?', "ground_truth": ""},
    {"category_id": "1", "question_id": "2", "question": 'What is the protocol used by "Receipt Delivery"?', "ground_truth": ""},
    {"category_id": "1", "question_id": "3", "question": 'What is the protocol used by "Customer Profile Lookup"?', "ground_truth": ""},
    {"category_id": "1", "question_id": "4", "question": 'What is the cost of "Immutable Append-Only Log Storage"?', "ground_truth": ""},
    {"category_id": "1", "question_id": "5", "question": 'What is the implementation status of "Return Eligibility Verification Engine"?', "ground_truth": ""},

    # Category 2: 1 hop relationship traversal queries
    {"category_id": "2", "question_id": "6", "question": 'Which data flows are inputs to "Screen for Fraud"?', "ground_truth": ""},
    {"category_id": "2", "question_id": "7", "question": 'Which data store receives "Refund Execution Audit Entry"?', "ground_truth": ""},
    {"category_id": "2", "question_id": "8", "question": 'Which is the following task after "Ship Order"?', "ground_truth": ""},
    {"category_id": "2", "question_id": "9", "question": 'Which is the following task after "Display Return Policy"?', "ground_truth": ""},
    {"category_id": "2", "question_id": "10", "question": 'Which are the possible mitigations for threat "Payment Data Tampering in Transit"?', "ground_truth": ""},

    # Category 3: 2 hop relationship traversal queries
    {"category_id": "3", "question_id": "11", "question": 'What threats are linked to "Generate Delivery Milestone"?', "ground_truth": ""},
    {"category_id": "3", "question_id": "12", "question": 'What categories are the mitigations which can counter threat named "Sensitive Data Leakage in Receipts"?', "ground_truth": ""},
    {"category_id": "3", "question_id": "13", "question": 'Which trust boundaries are crossed by the data flows that are input to "Execute Refund"?', "ground_truth": ""},
    {"category_id": "3", "question_id": "14", "question": 'What trust zone does the data store that stores "Payment Record Storage" reside in?', "ground_truth": ""},
    {"category_id": "3", "question_id": "15", "question": 'What mitigations are implemented to data store "Fraud Rules Repository"?', "ground_truth": ""},

    # Category 4: 3 hop relationship traversal queries
    {"category_id": "4", "question_id": "16", "question": 'What threats impact the data flows which are outputted by the process "Execute Payment Transaction"?', "ground_truth": ""},
    {"category_id": "4", "question_id": "17", "question": 'What threats impact the data flows which cross the trust boundary named "Internal Order Management Zone (1)"?', "ground_truth": ""},
    {"category_id": "4", "question_id": "18", "question": 'What mitigations are implemented for the processes residing in trust zone named "Internal Network Boundary (2)"?', "ground_truth": ""},
    {"category_id": "4", "question_id": "19", "question": 'What mitigations secure the data flows stored by the data store "Customer Database"?', "ground_truth": ""},
    {"category_id": "4", "question_id": "20", "question": 'What threats impact the external entity which sends the data flow named "Carrier Tracking Update"?', "ground_truth": ""},

    # Category 5: 4 hop relationship traversal queries
    {"category_id": "5", "question_id": "21", "question": 'What categories are the threats impacting the data flows which are inputs for the process "Publish Approved Review"?', "ground_truth": ""},
    {"category_id": "5", "question_id": "22", "question": 'What categories are the mitigations which can counter the threats affecting data store "Audit Log"?', "ground_truth": ""},
    {"category_id": "5", "question_id": "23", "question": 'What categories are the mitigations which can counter the threats affecting data store "Order and Shipment Database"?', "ground_truth": ""},
    {"category_id": "5", "question_id": "24", "question": 'What threats impact the process which outputs the data flow which is stored by data store "Inventory Database"?', "ground_truth": ""},
    {"category_id": "5", "question_id": "25", "question": 'What mitigations are used for the process which outputs the data flow that is taken as input by process "Assess Return Eligibility"?', "ground_truth": ""},

    # Category 6: BPMN to DFD decomposition traceability queries
    {"category_id": "6", "question_id": "26", "question": 'What are the external entities from the "Process Payment" BPMN Sub-Process?', "ground_truth": ""},
    {"category_id": "6", "question_id": "27", "question": 'What are the data stores from the "Manage Customer Profile" BPMN Sub-Process?', "ground_truth": ""},
    {"category_id": "6", "question_id": "28", "question": 'What threats affect the processes from the DFD decomposition of "Process Tracking Update & Notify Customer" BPMN Sub-Process?', "ground_truth": ""},
    {"category_id": "6", "question_id": "29", "question": 'What are the risk levels of threats affecting processes from the DFD decomposition of "Submit and Moderate Review" BPMN Sub-Process?', "ground_truth": ""},
    {"category_id": "6", "question_id": "30", "question": 'What are the trust zones from the DFD Decomposition of "Process Return & Issue Refund" BPMN Sub-Process?', "ground_truth": ""},

    # Category 7: Threat-to-Element Mapping
    {"category_id": "7", "question_id": "31", "question": 'What threats affect the "Screen for Fraud" process?', "ground_truth": ""},
    {"category_id": "7", "question_id": "32", "question": 'What are the threats affecting the "Execute Payment Transaction" process?', "ground_truth": ""},
    {"category_id": "7", "question_id": "33", "question": 'What are the threats affecting the "Session Store" data store?', "ground_truth": ""},
    {"category_id": "7", "question_id": "34", "question": 'What are the threats affecting the "Content Moderation Service (ModerateAI)" external entity?', "ground_truth": ""},
    {"category_id": "7", "question_id": "35", "question": 'What are the threats affecting the "Order and Shipment Database" data store?', "ground_truth": ""},

    # Category 8: Mitigation-to-Threat Mapping
    {"category_id": "8", "question_id": "36", "question": 'Which threats does "Immutable Append-Only Log Storage" mitigate?', "ground_truth": ""},
    {"category_id": "8", "question_id": "37", "question": 'Which mitigations are defined for "Transaction Repudiation"?', "ground_truth": ""},
    {"category_id": "8", "question_id": "38", "question": 'Which mitigations are defined for "Refund Amount Escalation"?', "ground_truth": ""},
    {"category_id": "8", "question_id": "39", "question": 'Which threats does "Carrier API Key Authentication and IP Allowlisting" mitigate?', "ground_truth": ""},
    {"category_id": "8", "question_id": "40", "question": 'Which mitigations are defined for "Refund Repudiation"?', "ground_truth": ""},

    # Category 9: Cross-case reuse and same-entity traceability queries
    {"category_id": "9", "question_id": "41", "question": 'To what processes is the external entity "Customer" sending data flows across all cases?', "ground_truth": ""},
    {"category_id": "9", "question_id": "42", "question": 'What data flows are being sent by external entity "Payment Gateway Provider (StripeConnect)" across all cases?', "ground_truth": ""},
    {"category_id": "9", "question_id": "43", "question": 'To what threats is the data store "Customer Database" exposed across all cases?', "ground_truth": ""},
    {"category_id": "9", "question_id": "44", "question": 'What mitigations are defined for the data flows stored by data store "Audit Log" across all cases?', "ground_truth": ""},
    {"category_id": "9", "question_id": "45", "question": 'What threats are being mitigated by mitigation "Comprehensive Transaction Logging" across all cases?', "ground_truth": ""},

    # Category 10: Multi-hop end-to-end path queries
    {"category_id": "10", "question_id": "46", "question": 'Trace the path from process "Screen for Fraud" to data store "Payment Records".', "ground_truth": ""},
    {"category_id": "10", "question_id": "47", "question": 'Trace the path from external entity "Payment Gateway Provider (StripeConnect)" to external entity "Customer".', "ground_truth": ""},
    {"category_id": "10", "question_id": "48", "question": 'Trace the path from external entity "Customer" to external entity "Email Delivery Service (SendGrid)".', "ground_truth": ""},
    {"category_id": "10", "question_id": "49", "question": 'Trace the path from process "Receive and Validate Review" to data store "Product Reviews Database".', "ground_truth": ""},
    {"category_id": "10", "question_id": "50", "question": 'Trace the path from process "Validate Return Request" to external entity "Payment Gateway Provider (StripeConnect)".', "ground_truth": ""},

    # Category 11: Multiple intent questions
    {"category_id": "11", "question_id": "51", "question": 'What is the risk level of "Carrier Identity Spoofing", and what trust boundary does "Ingest & Validate Carrier Update" reside in?', "ground_truth": ""},
    {"category_id": "11", "question_id": "52", "question": 'Which mitigations are linked to "Refund Repudiation", and what protocol is used by "Refund Authorization Request"?', "ground_truth": ""},
    {"category_id": "11", "question_id": "53", "question": 'What threats affect "Screen for Fraud" and what mitigations are applied to "Fraud Rules Repository"?', "ground_truth": ""},
    {"category_id": "11", "question_id": "54", "question": 'What trust boundaries are crossed by "Approved Payment Request" and what threats affect "Generate Payment Receipt"?', "ground_truth": ""},
    {"category_id": "11", "question_id": "55", "question": 'What is the implementation status of "Return Eligibility Verification Engine", and what data store receives "Return Processing Audit Entry"?', "ground_truth": ""},
]

questions_truths_list = [
    # Category 1: Direct relation queries
    {"""category_id""": """1""", """question_id""": """1""", """question""": """What is the risk level of "Carrier Identity Spoofing"?""", """ground_truth""": """The risk level of "Carrier Identity Spoofing" is "Critical"."""},
    {"""category_id""": """1""", """question_id""": """2""", """question""": """What is the protocol used by "Receipt Delivery"?""", """ground_truth""": """The protocol used by "Receipt Delivery" is "HTTPS"."""},
    {"""category_id""": """1""", """question_id""": """3""", """question""": """What is the protocol used by "Customer Profile Lookup"?""", """ground_truth""": """The protocol used by "Customer Profile Lookup" is "TLS"."""},
    {"""category_id""": """1""", """question_id""": """4""", """question""": """What is the cost of "Immutable Append-Only Log Storage"?""", """ground_truth""": """The cost of "Immutable Append-Only Log Storage" is 14,000."""},
    {"""category_id""": """1""", """question_id""": """5""", """question""": """What is the implementation status of "Return Eligibility Verification Engine"?""", """ground_truth""": """The implementation status of "Return Eligibility Verification Engine" is "Implemented"."""},

    # Category 2: 1 hop relationship traversal queries
    {"""category_id""": """2""", """question_id""": """6""", """question""": """Which data flows are inputs to "Screen for Fraud"?""", """ground_truth""": """The data flows that are inputs to "Screen for Fraud" are "Validated Payment Request" and "Fraud Scoring Response"."""},
    {"""category_id""": """2""", """question_id""": """7""", """question""": """Which data store receives "Refund Execution Audit Entry"?""", """ground_truth""": """The data store that receives "Refund Execution Audit Entry" is "Audit Log"."""},
    {"""category_id""": """2""", """question_id""": """8""", """question""": """Which is the following task after "Ship Order"?""", """ground_truth""": """The following task after "Ship Order" is "Update Delivery Status"."""},
    {"""category_id""": """2""", """question_id""": """9""", """question""": """Which is the following task after "Display Return Policy"?""", """ground_truth""": """The task following "Display Return Policy" is "Collect Return Reason"."""},
    {"""category_id""": """2""", """question_id""": """10""", """question""": """Which are the possible mitigations for threat "Payment Data Tampering in Transit"?""", """ground_truth""": """The possible mitigations for threat "Payment Data Tampering in Transit" are "TLS 1.3 with Certificate Pinning" and "Input Validation and Integrity Checks"."""},

    # Category 3: 2 hop relationship traversal queries
    {"""category_id""": """3""", """question_id""": """11""", """question""": """What threats are linked to "Generate Delivery Milestone"?""", """ground_truth""": """The threats linked to "Generate Delivery Milestone" are "Delivery Confirmation Repudiation" and "Customer Delivery Address Exposure"."""},
    {"""category_id""": """3""", """question_id""": """12""", """question""": """What categories are the mitigations which can counter threat named "Sensitive Data Leakage in Receipts"?""", """ground_truth""": """The mitigations that can counter the threat named "Sensitive Data Leakage in Receipts" are "PII Data Masking in Output" and "Encryption at Rest with RBAC"; their categories are "Data Protection"."""},
    {"""category_id""": """3""", """question_id""": """13""", """question""": """Which trust boundaries are crossed by the data flows that are input to "Execute Refund"?""", """ground_truth""": """The data flow "Approved Return for Refund" is input to "Execute Refund" and crosses the "Internal Returns Processing Zone" trust boundary and the "Financial Services Zone" trust boundary."""},
    {"""category_id""": """3""", """question_id""": """14""", """question""": """What trust zone does the data store that stores "Payment Record Storage" reside in?""", """ground_truth""": """The data store that stores "Payment Record Storage" resides within the "PCI Compliance Zone"."""},
    {"""category_id""": """3""", """question_id""": """15""", """question""": """What mitigations are implemented to data store "Fraud Rules Repository"?""", """ground_truth""": """The mitigations implemented to the data store "Fraud Rules Repository" are "Privileged Access Management"."""},

    # Category 4: 3 hop relationship traversal queries
    {"""category_id""": """4""", """question_id""": """16""", """question""": """What threats impact the data flows which are outputted by the process "Execute Payment Transaction"?""", """ground_truth""": """The threats impacting the data flows outputted by the process "Execute Payment Transaction" are "Gateway Communication Tampering" and "Sensitive Data Leakage in Receipts"."""},
    {"""category_id""": """4""", """question_id""": """17""", """question""": """What threats impact the data flows which cross the trust boundary named "Internal Order Management Zone (1)"?""", """ground_truth""": """The threats impacting the data flows which cross the trust boundary named "Internal Order Management Zone (1)" are "Shipment Tracking Data Tampering", "Delivery Audit Trail Gaps" and "Customer Delivery Address Exposure"."""},
    {"""category_id""": """4""", """question_id""": """18""", """question""": """What mitigations are implemented for the processes residing in trust zone named "Internal Network Boundary (2)"?""", """ground_truth""": """The mitigations implemented for the processes residing in the trust zone named "Internal Network Boundary (2)" are "Input Validation and Integrity Checks", "Multi-Factor Authentication", "Rate Limiting and Circuit Breaker", "Mutual TLS Authentication", "PII Data Masking in Output" and "Immutable Append-Only Log Storage"."""},
    {"""category_id""": """4""", """question_id""": """19""", """question""": """What mitigations secure the data flows stored by the data store "Customer Database"?""", """ground_truth""": """The mitigations that secure the data flows stored by the data store "Customer Database" are "Encryption at Rest with RBAC" and "Return Data Access Restrictions"."""},
    {"""category_id""": """4""", """question_id""": """20""", """question""": """What threats impact the external entity which sends the data flow named "Carrier Tracking Update"?""", """ground_truth""": """The threats that impact the external entity which sends the data flow named "Carrier Tracking Update" are "Carrier Identity Spoofing" and "Tracking Update Flooding"."""},

    # Category 5: 4 hop relationship traversal queries
    {"""category_id""": """5""", """question_id""": """21""", """question""": """What categories are the threats impacting the data flows which are outputs of the process "Publish Approved Review"?""", """ground_truth""": """The threats impacting the data flows which are outputs of the process "Publish Approved Review" are in the following categories: "Tampering" and "Information Disclosure"."""},
    {"""category_id""": """5""", """question_id""": """22""", """question""": """What categories are the mitigations which can counter the threats affecting data store "Audit Log"?""", """ground_truth""": """The mitigation categories for mitigations that can counter threats affecting the data store "Audit Log" are "Logging & Monitoring" and "Access Control"."""},
    {"""category_id""": """5""", """question_id""": """23""", """question""": """What categories are the mitigations which can counter the threats affecting data store "Order and Shipment Database"?""", """ground_truth""": """The mitigations which can counter the threats affecting data store "Order and Shipment Database" are in the categories "Input Validation" and "Data Protection"."""},
    {"""category_id""": """5""", """question_id""": """24""", """question""": """What threats impact the process which outputs the data flow which is stored by data store "Inventory Database"?""", """ground_truth""": """The threats that impact the process which outputs the data flow stored by the data store "Inventory Database" are "Return Condition Data Tampering", "Return Record Falsification" and "Fraudulent Return Request Spoofing"."""},
    {"""category_id""": """5""", """question_id""": """25""", """question""": """What mitigations are used for the process which outputs the data flow that is taken as input by process "Assess Return Eligibility"?""", """ground_truth""": """The mitigations used for the process which outputs the data flow taken as input by process "Assess Return Eligibility" are "Return Eligibility Verification Engine" and "Input Validation and Integrity Checks"."""},

    # Category 6: BPMN to DFD decomposition traceability queries
    {"""category_id""": """6""", """question_id""": """26""", """question""": """What are the external entities from the "Process Payment" BPMN Sub-Process?""", """ground_truth""": """The external entities from the DFD decomposition of "Process Payment" are "Customer", "Payment Gateway Provider (StripeConnect)", and "Fraud Detection Service (FraudShield)"."""},
    {"""category_id""": """6""", """question_id""": """27""", """question""": """What are the data stores from the "Manage Customer Profile" BPMN Sub-Process?""", """ground_truth""": """The data stores from the DFD decomposition of the "Manage Customer Profile" BPMN Sub-Process are "Customer Database", "Audit Log", and "Session Store"."""},
    {"""category_id""": """6""", """question_id""": """28""", """question""": """What threats affect the processes from the DFD decomposition of "Process Tracking Update & Notify Customer" BPMN Sub-Process?""", """ground_truth""": """The threats that affect the processes from the DFD decomposition of "Process Tracking Update & Notify Customer" BPMN Sub-Process are "Carrier Identity Spoofing", "Shipment Tracking Data Tampering", "Carrier API Privilege Escalation", "Delivery Confirmation Repudiation", "Order Status Record Tampering", "Notification Content Spoofing" and "Customer Delivery Address Exposure"."""},
    {"""category_id""": """6""", """question_id""": """29""", """question""": """What are the threats and risk levels of threats affecting processes from the DFD decomposition of "Submit and Moderate Review" BPMN Sub-Process?""", """ground_truth""": """The risk levels of threats affecting processes from the DFD decomposition of "Submit and Moderate Review" BPMN Sub-Process are: "Critical" for "Fake Review Identity Spoofing", "Low" for "Review Authorship Denial", "Medium" for "Review Submission Flooding", "High" for "Moderation Bypass via Content Obfuscation", "Medium" for "Moderation Decision Repudiation", "High" for "Review Score Tampering in Database" and "Medium" for "Reviewer Purchase History Exposure"."""},
    {"""category_id""": """6""", """question_id""": """30""", """question""": """What are the trust zones from the DFD Decomposition of "Process Return & Issue Refund" BPMN Sub-Process?""", """ground_truth""": """The trust zones from the DFD decomposition of the "Process Return & Issue Refund" BPMN Sub-Process are "Internal Returns Processing Zone" and "Financial Services Zone"."""},

    # Category 7: Threat-to-Element Mapping
    {"""category_id""": """7""", """question_id""": """31""", """question""": """What threats affect the "Screen for Fraud" process?""", """ground_truth""": """The threats that affect the "Screen for Fraud" process are "Fraud Screening Denial of Service", "Fraud Service Response Spoofing", and "Transaction Repudiation"."""},
    {"""category_id""": """7""", """question_id""": """32""", """question""": """What are the threats affecting the "Execute Payment Transaction" process?""", """ground_truth""": """The threats affecting the "Execute Payment Transaction" process are "Transaction Repudiation" and "Payment Record Tampering"."""},
    {"""category_id""": """7""", """question_id""": """33""", """question""": """What are the threats affecting the "Session Store" data store?""", """ground_truth""": """The threats affecting the "Session Store" data store are "Session Fixation Attack" and "Account Takeover via Credential Stuffing"."""},
    {"""category_id""": """7""", """question_id""": """34""", """question""": """What are the threats affecting the "Content Moderation Service (ModerateAI)" external entity?""", """ground_truth""": """The threats affecting the "Content Moderation Service (ModerateAI)" external entity are "Moderation Bypass via Content Obfuscation"."""},
    {"""category_id""": """7""", """question_id""": """35""", """question""": """What are the threats affecting the "Order and Shipment Database" data store?""", """ground_truth""": """The threats affecting the "Order and Shipment Database" data store are "Order Status Record Tampering" and "Customer Delivery Address Exposure"."""},

    # Category 8: Mitigation-to-Threat Mapping
    {"""category_id""": """8""", """question_id""": """36""", """question""": """Which threats can "Immutable Append-Only Log Storage" mitigate?""", """ground_truth""": """\"Immutable Append-Only Log Storage\" can mitigate the following threats: "Transaction Repudiation", "Audit Trail Tampering", "Refund Repudiation", "Moderation Decision Repudiation", "Review Score Tampering in Database", "Return Processing Audit Gap", "Delivery Audit Trail Gaps", "Payment Record Tampering" and "Audit Log Bypass on Profile Changes"."""},
    {"""category_id""": """8""", """question_id""": """37""", """question""": """Which mitigations are defined for "Transaction Repudiation"?""", """ground_truth""": """The mitigations defined for "Transaction Repudiation" are "Comprehensive Transaction Logging" and "Immutable Append-Only Log Storage"."""},
    {"""category_id""": """8""", """question_id""": """38""", """question""": """Which mitigations are defined for "Refund Amount Escalation"?""", """ground_truth""": """The mitigations defined for "Refund Amount Escalation" are "Refund Amount Validation and Caps" and "Refund Authorization Workflow"."""},
    {"""category_id""": """8""", """question_id""": """39""", """question""": """Which threats does "Carrier API Key Authentication and IP Allowlisting" mitigate?""", """ground_truth""": """\"Carrier API Key Authentication and IP Allowlisting\" mitigates "Carrier Identity Spoofing" and "Carrier API Privilege Escalation"."""},
    {"""category_id""": """8""", """question_id""": """40""", """question""": """Which mitigations are defined for "Refund Repudiation"?""", """ground_truth""": """The mitigations defined for "Refund Repudiation" are "Comprehensive Transaction Logging", "Refund Authorization Workflow", and "Immutable Append-Only Log Storage"."""},

    # Category 9: Cross-case reuse and same-entity traceability queries
    {"""category_id""": """9""", """question_id""": """41""", """question""": """To what processes is the external entity "Customer" sending data flows across all cases?""", """ground_truth""": """Across all cases, the external entity "Customer" is sending data flows to the following processes: "Validate Payment Details", "Authenticate and Authorize User", "Receive and Validate Review", "Validate Return Request", and "Validate & Apply Profile Changes"."""},
    {"""category_id""": """9""", """question_id""": """42""", """question""": """What data flows are being sent by external entity "Payment Gateway Provider (StripeConnect)" across all cases?""", """ground_truth""": """The data flows being sent by external entity "Payment Gateway Provider (StripeConnect)" across all cases are "Transaction Authorization Response" and "Refund Authorization Response"."""},
    {"""category_id""": """9""", """question_id""": """43""", """question""": """To what threats is the data store "Customer Database" exposed across all cases?""", """ground_truth""": """Across all cases, the data store "Customer Database" is exposed to the following threats: "Unauthorized Access to Customer PII", "Customer Identity Spoofing", "Profile Data Tampering", "Account Enumeration Attack", "Return Record Falsification" and "Customer Order History Exposure in Returns"."""},
    {"""category_id""": """9""", """question_id""": """44""", """question""": """What mitigations are defined for the data flows stored by data store "Audit Log" across all cases?""", """ground_truth""": """The mitigations defined for the data flows stored by the data store "Audit Log" across all cases are "Immutable Append-Only Log Storage", "Comprehensive Transaction Logging", "Delivery Confirmation Evidence Chain", "Detailed Profile Change Audit Trail", "End-to-End Delivery Audit Trail" and "Return Processing Audit Trail"."""},
    {"""category_id""": """9""", """question_id""": """45""", """question""": """What threats are being mitigated by mitigation "Comprehensive Transaction Logging" across all cases?""", """ground_truth""": """The threats being mitigated by "Comprehensive Transaction Logging" across all cases are "Transaction Repudiation", "Audit Trail Tampering", "Unauthorized Profile Change Repudiation", "Review Authorship Denial", "Refund Repudiation", and "Delivery Audit Trail Gaps"."""},

    # Category 10: Multi-hop end-to-end path queries
    {"""category_id""": """10""", """question_id""": """46""", """question""": """Trace the path from process "Screen for Fraud" to data store "Payment Records".""", """ground_truth""": """The path from "Screen for Fraud" to "Payment Records" is: "Screen for Fraud" outputs data flow "Approved Payment Request", which is input to "Execute Payment Transaction", which outputs data flow "Payment Record Storage", which is stored by "Payment Records"."""},
    {"""category_id""": """10""", """question_id""": """47""", """question""": """Trace the path from external entity "Payment Gateway Provider (StripeConnect)" to external entity "Customer".""", """ground_truth""": """The path from "Payment Gateway Provider (StripeConnect)" to "Customer" is "Payment Gateway Provider (StripeConnect)" sends data flow "Transaction Authorization Response" which is input to "Execute Payment Transaction" which outputs data flow "Receipt Generation Data" which is input to "Generate Payment Receipt" which outputs data flow "Receipt Delivery" which is received by "Customer"."""},
    {"""category_id""": """10""", """question_id""": """48""", """question""": """Trace the path from external entity "Customer" to external entity "Email Delivery Service (SendGrid)".""", """ground_truth""": """The path from external entity "Customer" to external entity "Email Delivery Service (SendGrid)" is "Customer" sends data flow "Profile Modification Submission" which is input to "Validate and Apply Profile Changes" which outputs data flow "Notification Trigger" which is input to "Dispatch Notification" which outputs data flow "Email Dispatch Request" which is received by "Email Delivery Service (SendGrid)"."""},
    {"""category_id""": """10""", """question_id""": """49""", """question""": """Trace the path from process "Receive and Validate Review" to data store "Product Reviews Database".""", """ground_truth""": """The path from "Receive and Validate Review" to "Product Reviews Database" is "Receive and Validate Review" outputs data flow "Validated Review Handoff" which is input to "Screen Review Content" which outputs data flow "Approved Review for Publication" which is input to "Publish Approved Review" which outputs data flow "Published Review Storage" which is stored in "Product Reviews Database"."""},
    {"""category_id""": """10""", """question_id""": """50""", """question""": """Trace the path from process "Validate Return Request" to external entity "Payment Gateway Provider (StripeConnect)".""", """ground_truth""": """The path from "Validate Return Request" to "Payment Gateway Provider (StripeConnect)" is "Validate Return Request" outputs data flow "Validated Return for Assessment" which is input to "Assess Return Eligibility" which outputs data flow "Approved Return for Refund" which is input to "Execute Refund" which outputs data flow "Refund Authorization Request" which is received by "Payment Gateway Provider (StripeConnect)"."""},

    # Category 11: Multiple intent questions
    {"""category_id""": """11""", """question_id""": """51""", """question""": """What is the risk level of "Carrier Identity Spoofing", and what trust boundary does "Ingest & Validate Carrier Update" reside in?""", """ground_truth""": """The risk level of "Carrier Identity Spoofing" is "Critical", and the "Ingest and Validate Carrier Update" process resides inside the "Carrier Integration Zone" trust boundary."""},
    {"""category_id""": """11""", """question_id""": """52""", """question""": """Which mitigations are linked to "Refund Repudiation", and what protocol is used by "Refund Authorization Request"?""", """ground_truth""": """The mitigations linked to "Refund Repudiation" are "Comprehensive Transaction Logging", "Refund Authorization Workflow", and "Immutable Append-Only Log Storage". The protocol used by "Refund Authorization Request" is "HTTPS"."""},
    {"""category_id""": """11""", """question_id""": """53""", """question""": """What threats affect "Screen for Fraud" and what mitigations are applied to "Fraud Rules Repository"?""", """ground_truth""": """The threats that affect "Screen for Fraud" are "Fraud Screening Denial of Service", "Fraud Service Response Spoofing", and "Transaction Repudiation". The mitigations applied to "Fraud Rules Repository" are "Privileged Access Management"."""},
    {"""category_id""": """11""", """question_id""": """54""", """question""": """What trust boundaries are crossed by "Approved Payment Request" and what threats affect "Generate Payment Receipt"?""", """ground_truth""": """The trust boundaries crossed by "Approved Payment Request" are the "Internal Network Boundary" and the "PCI Compliance Zone". The threats that affect "Generate Payment Receipt" are "Sensitive Data Leakage in Receipts" and "Audit Trail Tampering"."""},
    {"""category_id""": """11""", """question_id""": """55""", """question""": """What is the implementation status of "Return Eligibility Verification Engine", and what data store receives "Return Processing Audit Entry"?""", """ground_truth""": """The implementation status of "Return Eligibility Verification Engine" is "Implemented", and the data store that receives "Return Processing Audit Entry" is "Audit Log"."""},
]

questions_list_owasp = [
    # Category 1: Direct Attribute Retrieval
    {
        "category_id": "C1",
        "question_id": "C1_Q1",
        "question": "What is the score and severity of the threat 'Patient Data Exfiltration'?",
        "ground_truth": ""
    },
    {
        "category_id": "C1",
        "question_id": "C1_Q2",
        "question": "What is the severity of the threat 'Physician Identity Spoofing'?",
        "ground_truth": ""
    },
    {
        "category_id": "C1",
        "question_id": "C1_Q3",
        "question": "How long is the regulatory deadline for substance reporting in the case of threat 'Controlled Substance Reporting Denial of Service'?",
        "ground_truth": ""
    },
    # Category 2: Element-to-Threat/Mitigation Relationships (1-hop)
    {
        "category_id": "C2",
        "question_id": "C2_Q1",
        "question": "What threats is the 'Patient' external entity susceptible to?",
        "ground_truth": ""
    },
    {
        "category_id": "C2",
        "question_id": "C2_Q2",
        "question": "Which threats affect the 'Pharmacy Dispensing & Inventory Records', and what are their risk levels?",
        "ground_truth": ""
    },
    {
        "category_id": "C2",
        "question_id": "C2_Q3",
        "question": "What threats are assigned to the process 'Manage Clinical Records', and what is the severity of each?",
        "ground_truth": ""
    },
    # Category 3: Threat-to-Mitigation Mapping (1-hop)
    {
        "category_id": "C3",
        "question_id": "C3_Q1",
        "question": "Which mitigations address the threat 'Unauthorized Clinical Record Modification'?",
        "ground_truth": ""
    },
    {
        "category_id": "C3",
        "question_id": "C3_Q2",
        "question": "What mitigations are linked to 'Controlled Substance Dispensing Record Deletion', and what are their descriptions?",
        "ground_truth": ""
    },
    {
        "category_id": "C3",
        "question_id": "C3_Q3",
        "question": "Which single mitigation addresses 'Eligibility Process Elevation of Privilege'?",
        "ground_truth": ""
    },
    # Category 4: Cross-Element and Cross-Case Traversal (1-2 hops)
    {
        "category_id": "C4",
        "question_id": "C4_Q1",
        "question": "Which mitigations address the threats affecting the process 'Dispense Medication'?",
        "ground_truth": ""
    },
    {
        "category_id": "C4",
        "question_id": "C4_Q2",
        "question": "Which mitigations address the threats affecting the data store 'Insurance Claims Repository'?",
        "ground_truth": ""
    },
    {
        "category_id": "C4",
        "question_id": "C4_Q3",
        "question": "What threats is the 'Electronic Health Records Database' data store susceptible to across all cases?",
        "ground_truth": ""
    },
    # Category 5: DFD Diagram Paths
    {
        "category_id": "C5",
        "question_id": "C5_Q1",
        "question": "What process takes as input the data flow outputted by process 'Patient Registration Gateway'?",
        "ground_truth": ""
    },
    {
        "category_id": "C5",
        "question_id": "C5_Q2",
        "question": "What processes take as input the data flows provided by data store 'Electronic Health Records Database'?",
        "ground_truth": ""
    },
    {
        "category_id": "C5",
        "question_id": "C5_Q3",
        "question": "What data stores store data flows outputted by the process 'Dispense Medication'?",
        "ground_truth": ""
    },
]

questions_truths_list_owasp = [
    # Category 1: Direct Attribute Retrieval
    {
        "category_id": 1,
        "question_id": 1,
        "question": 'What is the score and severity of the threat "Patient Data Exfiltration"?',
        "ground_truth": 'The score of the threat "Patient Data Exfiltration" is 9.2, and the severity is Critical.'
    },
    {
        "category_id": 1,
        "question_id": 2,
        "question": 'What is the severity of the threat "Physician Identity Spoofing"?',
        "ground_truth": 'The severity of the threat "Physician Identity Spoofing" is High.'
    },
    {
        "category_id": 1,
        "question_id": 3,
        "question": 'How long is the regulatory deadline for substance reporting in the case of threat "Controlled Substance Reporting Denial of Service"?',
        "ground_truth": 'The regulatory deadline for substance reporting in the case of the threat "Controlled Substance Reporting Denial of Service" is 24 hours.'
    },
    # Category 2: Element-to-Threat/Mitigation Relationships (1-hop)
    {
        "category_id": 2,
        "question_id": 4,
        "question": 'What threats is the "Patient" external entity susceptible to?',
        "ground_truth": 'The "Patient" external entity is susceptible to "Patient Identity Spoofing" and "Patient Action Repudiation".'
    },
    {
        "category_id": 2,
        "question_id": 5,
        "question": 'Which threats affect the "Pharmacy Dispensing & Inventory Records", and what are their risk levels?',
        "ground_truth": 'The threats that affect "Pharmacy Dispensing & Inventory Records" are "Controlled Substance Dispensing Record Deletion" with a risk level of Critical.'
    },
    {
        "category_id": 2,
        "question_id": 6,
        "question": 'What threats are assigned to the process "Manage Clinical Records", and what is the severity of each?',
        "ground_truth": 'The threats assigned to the process "Manage Clinical Records" are "Unauthorized Clinical Record Modification" with severity Critical, "Clinical Record Access Repudiation" with severity High, and "Patient Data Exfiltration" with severity Critical.'
    },
    # Category 3: Threat-to-Mitigation Mapping (1-hop)
    {
        "category_id": 3,
        "question_id": 7,
        "question": 'Which mitigations address the threat "Unauthorized Clinical Record Modification"?',
        "ground_truth": 'The mitigations that address the threat "Unauthorized Clinical Record Modification" are "Clinical Record Versioning with Change Tracking" and "Dual Authorization for Critical Record Changes".'
    },
    {
        "category_id": 3,
        "question_id": 8,
        "question": 'What mitigations are linked to "Controlled Substance Dispensing Record Deletion", and what are their descriptions?',
        "ground_truth": 'The mitigations linked to "Controlled Substance Dispensing Record Deletion" are "Dispensing Record Cryptographic Sealing" and "Append-Only Controlled Substance Ledger". The description of "Dispensing Record Cryptographic Sealing" is: "Each dispensing record is sealed with a cryptographic hash of its key fields (prescription ID, medication code, quantity, patient ID, timestamp, dispensing pharmacist). The hash is stored separately and verified on every read, enabling immediate detection of any post-creation modification.". The description of "Append-Only Controlled Substance Ledger" is: "All controlled substance dispensing events are additionally written to a dedicated append-only ledger on WORM storage, separate from the main dispensing records. This ledger cannot be modified or deleted even by database administrators, providing a tamper-proof audit trail for regulatory inspections.".'
    },
    {
        "category_id": 3,
        "question_id": 9,
        "question": 'Which single mitigation addresses "Eligibility Process Elevation of Privilege"?',
        "ground_truth": 'The single mitigation that addresses "Eligibility Process Elevation of Privilege" is "DMZ Service Account Isolation and Least Privilege".'
    },
    # Category 4: Cross-Element and Cross-Case Traversal (1-2 hops)
    {
        "category_id": 4,
        "question_id": 10,
        "question": 'Which mitigations address the threats affecting the process "Dispense Medication"?',
        "ground_truth": 'The mitigations that address the threats affecting the process "Dispense Medication" are "Dispensing Record Cryptographic Sealing" and "Resilient Reporting Queue with Guaranteed Delivery".'
    },
    {
        "category_id": 4,
        "question_id": 11,
        "question": 'Which mitigations address the threats affecting the data store "Insurance Claims Repository"?',
        "ground_truth": 'The mitigations that address the threats affecting the data store "Insurance Claims Repository" are "Claims Record Integrity Hashing" and "Insurance Data Role-Based Access Control".'
    },
    {
        "category_id": 4,
        "question_id": 12,
        "question": 'What threats is the "Electronic Health Records Database" data store susceptible to across all cases?',
        "ground_truth": 'The "Electronic Health Records Database" data store is susceptible to the following threats across all cases: "EHR Database Record Tampering", "Unauthorized EHR Data Disclosure", "EHR Database Denial of Service", "Unauthorized Patient Medication History Disclosure" and "EHR Medication Data Tampering via Pharmacy Channel".'
    },
    # Category 5: DFD Diagram Paths
    {
        "category_id": 5,
        "question_id": 13,
        "question": 'What process takes as input the data flow outputted by process "Patient Registration Gateway" and what is the name of the data flow?',
        "ground_truth": 'The process that takes as input the data flow outputted by process "Patient Registration Gateway" is "Verify Insurance Eligibility", which receives the "Insurance Verification Request" data flow from "Patient Registration Gateway".'
    },
    {
        "category_id": 5,
        "question_id": 14,
        "question": 'What processes take as input the data flows provided by data store "Electronic Health Records Database"?',
        "ground_truth": 'The process that take as input the data flows provided by the data store "Electronic Health Records Database" is "Check Drug Interactions".'
    },
    {
        "category_id": 5,
        "question_id": 15,
        "question": 'What data stores store data flows outputted by the process "Dispense Medication"?',
        "ground_truth": 'The data stores that store data flows outputted by the process "Dispense Medication" are "Pharmacy Dispensing & Inventory Records" and "Clinical Audit Trail".'
    },
    # Category 6: Trust Boundaries / Trust Zones
    {
        "category_id": 6,
        "question_id": 16,
        "question": 'Which data flows cross the "Hospital Perimeter Network" trust boundary?',
        "ground_truth": 'The data flows which cross the "Hospital Perimeter Network" trust boundary are: "Duplicate Record Check", "Registration Audit Log Entry", "Insurance Verification Result Storage", "Discharge Summary to Referring Physician" and "Discharge Summary to Patient".'
    },
    {
        "category_id": 6,
        "question_id": 17,
        "question": 'Which data flows cross the "Pharmacy Application Zone" trust boundary?',
        "ground_truth": 'The data flows which cross the "Pharmacy Application Zone" trust boundary are: "Prescription Processing Audit Entry", "Patient Allergy and Medication Query", "Allergy and Medication Response" and "Dispensing Audit Entry".'
    },
    {
        "category_id": 6,
        "question_id": 18,
        "question": 'In which trust zone do process "Receive & Validate Prescription" and data store "Insurance Claims Repository" reside in?',
        "ground_truth": 'Process "Receive & Validate Prescription" resides in trust zone "Pharmacy Application Zone" and data store "Insurance Claims Repository" resides in trust zone "Internal Clinical Network".'
    },
    # Category 7: Element to Element Path Tracing
    {
        "category_id": 7,
        "question_id": 19,
        "question": 'Trace the path from "Prescribing Physician" to the data store "Clinical Audit Trail".',
        "ground_truth": 'The path from "Prescribing Physician" to "Clinical Audit Trail" is: "Prescribing Physician" sends data flow "E-Prescription Submission", which is input to "Receive & Validate Prescription", which outputs data flow "Prescription Processing Audit Entry", which is stored by "Clinical Audit Trail".'
    },
    {
        "category_id": 7,
        "question_id": 20,
        "question": 'Trace the path from "Patient" to the "Insurance Claims Repository" data store.',
        "ground_truth": 'The path from "Patient" to "Insurance Claims Repository" is: "Patient" sends data flow "Patient Registration Submission", which is input to "Patient Registration Gateway", which outputs data flow "Insurance Verification Request", which is input to "Verify Insurance Eligibility", which outputs data flow "Insurance Verification Result Storage" which is stored by "Insurance Claims Repository".'
    },
    {
        "category_id": 7,
        "question_id": 21,
        "question": 'Trace the path from "Referring Physician" to the data store "Electronic Health Records Database".',
        "ground_truth": 'The path from "Referring Physician" to "Electronic Health Records Database" is: "Referring Physician" sends data flow "Physician Referral Submission", which is input to "Patient Registration Gateway", which outputs data flow "Duplicate Record Check", which is stored by "Electronic Health Records Database".'
    },
]