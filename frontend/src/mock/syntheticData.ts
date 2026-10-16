import { 
  GraphNodeData, 
  GraphEdgeData, 
  SuspiciousAlert, 
  CaseFile, 
  TimelineEvent, 
  ComplaintRecord 
} from '../types';

export const SYNTHETIC_NODES: GraphNodeData[] = [
  // Cluster Alpha: Mule Ring & Device Collusion (Operation Chakravyuh)
  {
    id: 'ACC_VICTIM_1',
    label: 'anand.verma@okaxis',
    type: 'account',
    role: 'source_victim',
    riskScore: 12,
    status: 'flagged',
    subText: 'Axis Bank • **** 9102',
    upiId: 'anand.verma@okaxis',
    accountNo: 'AXIS910238120',
    bankName: 'Axis Bank',
    tags: ['Source Account', 'Victim Drain', 'Reported Incident'],
  },
  {
    id: 'ACC_PRIMARY_MULE',
    label: 'rohit.sharma@paytm',
    type: 'account',
    role: 'aggregator_mule',
    riskScore: 96,
    status: 'flagged',
    subText: 'Paytm Payments Bank • **** 4421',
    upiId: 'rohit.sharma@paytm',
    accountNo: 'PYTM44219088',
    bankName: 'Paytm Bank',
    tags: ['Aggregator Hub', 'Rapid Dispersion', 'High Velocity'],
  },
  {
    id: 'ACC_MULE_2',
    label: 'karan.singh@icici',
    type: 'account',
    role: 'secondary_mule',
    riskScore: 92,
    status: 'flagged',
    subText: 'ICICI Bank • **** 1190',
    upiId: 'karan.singh@icici',
    accountNo: 'ICIC11903342',
    bankName: 'ICICI Bank',
    tags: ['Intermediary Mule', 'Quick Hop', 'Layer 2'],
  },
  {
    id: 'ACC_MULE_3',
    label: 'deepak.gupta@kotak',
    type: 'account',
    role: 'secondary_mule',
    riskScore: 89,
    status: 'flagged',
    subText: 'Kotak Bank • **** 6678',
    upiId: 'deepak.gupta@kotak',
    accountNo: 'KOTK66782291',
    bankName: 'Kotak Mahindra',
    tags: ['Intermediary Mule', 'Structuring Split', 'Layer 2'],
  },
  {
    id: 'ACC_MULE_4',
    label: 'amit.patel@oksbi',
    type: 'account',
    role: 'secondary_mule',
    riskScore: 94,
    status: 'flagged',
    subText: 'State Bank of India • **** 3320',
    upiId: 'amit.patel@oksbi',
    accountNo: 'SBIN33201109',
    bankName: 'SBI',
    tags: ['Intermediary Mule', 'Shared Device Collusion'],
  },
  {
    id: 'DEV_FARM_1',
    label: 'DEV-IMEI-889021-X9',
    type: 'device',
    role: 'device_farm',
    riskScore: 98,
    status: 'flagged',
    subText: 'OnePlus 11R • Android 14',
    deviceId: 'DEV-IMEI-889021-X9',
    deviceModel: 'OnePlus 11R (CPH2487)',
    tags: ['Device Farm', 'Multi-VPA Host', 'Rooted Hardware'],
  },
  {
    id: 'MERCH_CASHOUT',
    label: 'Kishan Electronics & Gold QR',
    type: 'merchant',
    role: 'cashout_merchant',
    riskScore: 88,
    status: 'flagged',
    subText: 'Merchant QR • MID-99042',
    merchantCategory: 'Consumer Electronics / Bullion',
    tags: ['Receiving Cashout Point', 'High Inflow Velocity', 'Off-Hours Spike'],
  },
  {
    id: 'COMPLAINT_NCRP_8812',
    label: 'NCRP-2026-8812',
    type: 'complaint',
    role: 'complaint',
    riskScore: 100,
    status: 'active',
    subText: 'Cyber Fraud FIR #412/26',
    complaintRef: 'NCRP-2026-8812',
    disputeAmount: 480000,
    tags: ['Extortion / APK Scam', 'High Priority Dispute'],
  },

  // Legitimate Baseline Nodes (for false positive & contrast evaluation)
  {
    id: 'ACC_LEGIT_1',
    label: 'priya.nair@okhdfc',
    type: 'account',
    role: 'verified_control',
    riskScore: 8,
    status: 'verified',
    subText: 'HDFC Bank • **** 5512',
    upiId: 'priya.nair@okhdfc',
    bankName: 'HDFC Bank',
    tags: ['Verified Salary Account', 'Regular Pattern'],
  },
  {
    id: 'MERCH_GROCERY',
    label: 'Reliance Fresh Store 44',
    type: 'merchant',
    role: 'verified_control',
    riskScore: 4,
    status: 'verified',
    subText: 'FMCG Retail • MID-10022',
    merchantCategory: 'Supermarket / Grocery',
    tags: ['Legitimate Merchant', 'Normal Operations'],
  },
  {
    id: 'DEV_USER_LEGIT',
    label: 'DEV-PIXEL-7A-LEGIT',
    type: 'device',
    role: 'verified_control',
    riskScore: 5,
    status: 'verified',
    subText: 'Pixel 7a • Android 14',
    deviceId: 'DEV-PIXEL-7A-LEGIT',
    deviceModel: 'Google Pixel 7a',
    tags: ['Single User Device'],
  }
];

export const SYNTHETIC_EDGES: GraphEdgeData[] = [
  // Fraud Ring flow
  {
    id: 'E_TXN_01',
    source: 'ACC_VICTIM_1',
    target: 'ACC_PRIMARY_MULE',
    amount: 480000,
    timestamp: '2026-10-15 10:02:11',
    utr: 'UTR20261015998012',
    channel: 'UPI_P2P',
    isSuspicious: true,
    ruleTriggered: 'RULE_ANOMALOUS_HIGH_VALUE_FIRST_TXN',
  },
  {
    id: 'E_TXN_02',
    source: 'ACC_PRIMARY_MULE',
    target: 'ACC_MULE_2',
    amount: 120000,
    timestamp: '2026-10-15 10:04:19',
    utr: 'UTR20261015998045',
    channel: 'UPI_P2P',
    isSuspicious: true,
    ruleTriggered: 'RULE_RAPID_DISPERSION_HOP1',
  },
  {
    id: 'E_TXN_03',
    source: 'ACC_PRIMARY_MULE',
    target: 'ACC_MULE_3',
    amount: 115000,
    timestamp: '2026-10-15 10:05:02',
    utr: 'UTR20261015998059',
    channel: 'UPI_P2P',
    isSuspicious: true,
    ruleTriggered: 'RULE_RAPID_DISPERSION_HOP1',
  },
  {
    id: 'E_TXN_04',
    source: 'ACC_PRIMARY_MULE',
    target: 'ACC_MULE_4',
    amount: 125000,
    timestamp: '2026-10-15 10:05:44',
    utr: 'UTR20261015998071',
    channel: 'UPI_P2P',
    isSuspicious: true,
    ruleTriggered: 'RULE_RAPID_DISPERSION_HOP1',
  },
  // Convergence to Cashout
  {
    id: 'E_TXN_05',
    source: 'ACC_MULE_2',
    target: 'MERCH_CASHOUT',
    amount: 118500,
    timestamp: '2026-10-15 10:08:12',
    utr: 'UTR20261015998110',
    channel: 'UPI_P2M',
    isSuspicious: true,
    ruleTriggered: 'RULE_CASHOUT_CONVERGENCE',
  },
  {
    id: 'E_TXN_06',
    source: 'ACC_MULE_3',
    target: 'MERCH_CASHOUT',
    amount: 114000,
    timestamp: '2026-10-15 10:09:05',
    utr: 'UTR20261015998124',
    channel: 'UPI_P2M',
    isSuspicious: true,
    ruleTriggered: 'RULE_CASHOUT_CONVERGENCE',
  },
  {
    id: 'E_TXN_07',
    source: 'ACC_MULE_4',
    target: 'MERCH_CASHOUT',
    amount: 123000,
    timestamp: '2026-10-15 10:09:55',
    utr: 'UTR20261015998139',
    channel: 'UPI_P2M',
    isSuspicious: true,
    ruleTriggered: 'RULE_CASHOUT_CONVERGENCE',
  },

  // Device Bindings (Shared device collusion!)
  {
    id: 'E_DEV_01',
    source: 'DEV_FARM_1',
    target: 'ACC_PRIMARY_MULE',
    amount: 0,
    timestamp: '2026-10-14 09:12:00',
    utr: 'BIND_889021_01',
    channel: 'DEVICE_BIND',
    isSuspicious: true,
    ruleTriggered: 'RULE_SHARED_DEVICE_CLUSTER',
  },
  {
    id: 'E_DEV_02',
    source: 'DEV_FARM_1',
    target: 'ACC_MULE_2',
    amount: 0,
    timestamp: '2026-10-14 09:40:15',
    utr: 'BIND_889021_02',
    channel: 'DEVICE_BIND',
    isSuspicious: true,
    ruleTriggered: 'RULE_SHARED_DEVICE_CLUSTER',
  },
  {
    id: 'E_DEV_03',
    source: 'DEV_FARM_1',
    target: 'ACC_MULE_3',
    amount: 0,
    timestamp: '2026-10-14 10:02:40',
    utr: 'BIND_889021_03',
    channel: 'DEVICE_BIND',
    isSuspicious: true,
    ruleTriggered: 'RULE_SHARED_DEVICE_CLUSTER',
  },
  {
    id: 'E_DEV_04',
    source: 'DEV_FARM_1',
    target: 'ACC_MULE_4',
    amount: 0,
    timestamp: '2026-10-14 10:15:22',
    utr: 'BIND_889021_04',
    channel: 'DEVICE_BIND',
    isSuspicious: true,
    ruleTriggered: 'RULE_SHARED_DEVICE_CLUSTER',
  },

  // Complaint link to Victim
  {
    id: 'E_CMP_01',
    source: 'COMPLAINT_NCRP_8812',
    target: 'ACC_VICTIM_1',
    amount: 480000,
    timestamp: '2026-10-15 10:14:00',
    utr: 'COMPLAINT_REF_8812',
    channel: 'COMPLAINT_LINK',
    isSuspicious: true,
    ruleTriggered: 'RULE_FORMAL_DISPUTE_FILED',
  },

  // Legitimate transfers
  {
    id: 'E_LEGIT_01',
    source: 'ACC_LEGIT_1',
    target: 'MERCH_GROCERY',
    amount: 1420,
    timestamp: '2026-10-15 11:30:10',
    utr: 'UTR20261015110488',
    channel: 'UPI_P2M',
    isSuspicious: false,
  },
  {
    id: 'E_DEV_LEGIT',
    source: 'DEV_USER_LEGIT',
    target: 'ACC_LEGIT_1',
    amount: 0,
    timestamp: '2026-08-10 12:00:00',
    utr: 'BIND_LEGIT_01',
    channel: 'DEVICE_BIND',
    isSuspicious: false,
  }
];

// Demo previous complaints with realistic status indicators (DEMO DATA)
export const DEMO_COMPLAINTS: ComplaintRecord[] = [
  {
    id: 'CMP0004',
    complaintRef: 'NCRP-CMP0004',
    date: '29 Sep 2026, 10:54 IST',
    shortDescription: 'Syndicate convergence victim; ₹10,732 routed via mule ACC0135 to collector ACC0140 within 58 seconds.',
    category: 'Rapid Onward Transfer / Convergence',
    disputeAmount: 10732.62,
    relatedAccountId: 'ACC0125',
    relatedAccountUpi: 'vikram.das125@synhdfc',
    relatedBeneficiaryUpi: 'vikram.reddy135@synicici',
    relatedBeneficiaryAccountId: 'ACC0135',
    relatedTxnUtr: 'TXN002804',
    riskLevel: 'CRITICAL',
    status: 'under_investigation',
    analystNotes: 'Complaint CMP0004: Victim ACC0125 -> Mule ACC0135 -> Collector ACC0140. High-velocity onward dispersion detected.',
  },
  {
    id: 'CMP0001',
    complaintRef: 'NCRP-CMP0001',
    date: '27 Sep 2026, 19:51 IST',
    shortDescription: 'Disputed UPI payment reported by HDFC account holder to unverified receiver.',
    category: 'Unauthorized UPI Debit',
    disputeAmount: 578.11,
    relatedAccountId: 'ACC0152',
    relatedAccountUpi: 'kabir.sharma152@synhdfc',
    relatedBeneficiaryUpi: 'ananya.das162@synsbi',
    relatedBeneficiaryAccountId: 'ACC0162',
    relatedTxnUtr: 'TXN002420',
    riskLevel: 'MEDIUM',
    status: 'resolved',
    analystNotes: 'Complaint CMP0001: Baseline individual dispute with no syndicate links. Settled by originating bank.',
  },
  {
    id: 'CMP0002',
    complaintRef: 'NCRP-CMP0002',
    date: '27 Sep 2026, 18:59 IST',
    shortDescription: 'Suspicious peer-to-peer fund transfer reported by Axis Bank complainant.',
    category: 'UPI Impersonation',
    disputeAmount: 2243.20,
    relatedAccountId: 'ACC0155',
    relatedAccountUpi: 'meera.das155@synaxis',
    relatedBeneficiaryUpi: 'meera.sharma165@synaxis',
    relatedBeneficiaryAccountId: 'ACC0165',
    relatedTxnUtr: 'TXN002648',
    riskLevel: 'MEDIUM',
    status: 'resolved',
    analystNotes: 'Complaint CMP0002: Standalone dispute. Chargeback processed; no mule ring topology found.',
  },
  {
    id: 'CMP0003',
    complaintRef: 'NCRP-CMP0003',
    date: '28 Sep 2026, 19:50 IST',
    shortDescription: 'Unrecognized debit from HDFC savings via QR collect mandate.',
    category: 'Collect Request Abuse',
    disputeAmount: 1573.11,
    relatedAccountId: 'ACC0154',
    relatedAccountUpi: 'kabir.reddy154@synhdfc',
    relatedBeneficiaryUpi: 'meera.das164@synsbi',
    relatedBeneficiaryAccountId: 'ACC0164',
    relatedTxnUtr: 'TXN002759',
    riskLevel: 'MEDIUM',
    status: 'pending_review',
    analystNotes: 'Complaint CMP0003: Collect request executed without user PIN confirmation. Audit requested.',
  },
  {
    id: 'CMP0005',
    complaintRef: 'NCRP-CMP0005',
    date: '29 Sep 2026, 18:59 IST',
    shortDescription: 'Disputed online payment transaction across synthetic Axis-to-HDFC corridor.',
    category: 'Phishing Reward Link',
    disputeAmount: 1037.38,
    relatedAccountId: 'ACC0153',
    relatedAccountUpi: 'isha.nair153@synaxis',
    relatedBeneficiaryUpi: 'meera.verma163@synhdfc',
    relatedBeneficiaryAccountId: 'ACC0163',
    relatedTxnUtr: 'TXN002868',
    riskLevel: 'MEDIUM',
    status: 'under_investigation',
    analystNotes: 'Complaint CMP0005: Suspected phishing link clicked via SMS notification.',
  },
  {
    id: 'CMP0006',
    complaintRef: 'NCRP-CMP0006',
    date: '30 Sep 2026, 11:47 IST',
    shortDescription: 'Syndicate convergence victim; ₹12,339 routed to mule ACC0133 forwarding to hub ACC0140.',
    category: 'Complaint Convergence / Syndicate',
    disputeAmount: 12339.28,
    relatedAccountId: 'ACC0123',
    relatedAccountUpi: 'ananya.singh123@synsbi',
    relatedBeneficiaryUpi: 'aarav.nair133@synsbi',
    relatedBeneficiaryAccountId: 'ACC0133',
    relatedTxnUtr: 'TXN002811',
    riskLevel: 'CRITICAL',
    status: 'under_investigation',
    analystNotes: 'Complaint CMP0006: Feeder mule ACC0133 forwarded 94% of victim funds to ACC0140 in 43 seconds.',
  },
  {
    id: 'CMP0007',
    complaintRef: 'NCRP-CMP0007',
    date: '30 Sep 2026, 17:57 IST',
    shortDescription: 'Syndicate convergence victim; ₹12,353 routed to mule ACC0132 forwarding to hub ACC0140.',
    category: 'Complaint Convergence / Syndicate',
    disputeAmount: 12353.66,
    relatedAccountId: 'ACC0122',
    relatedAccountUpi: 'ananya.sharma122@synsbi',
    relatedBeneficiaryUpi: 'rohan.nair132@synsbi',
    relatedBeneficiaryAccountId: 'ACC0132',
    relatedTxnUtr: 'TXN002858',
    riskLevel: 'CRITICAL',
    status: 'under_investigation',
    analystNotes: 'Complaint CMP0007: Part of S07 Complaint Convergence ring. Same day forward to Diya Das (ACC0140).',
  },
  {
    id: 'CMP0008',
    complaintRef: 'NCRP-CMP0008',
    date: '30 Sep 2026, 21:17 IST',
    shortDescription: 'Disputed Axis-to-ICICI transfer reported by cardholder.',
    category: 'Unauthorized UPI Debit',
    disputeAmount: 1792.02,
    relatedAccountId: 'ACC0151',
    relatedAccountUpi: 'vikram.singh151@synaxis',
    relatedBeneficiaryUpi: 'isha.gupta161@synicici',
    relatedBeneficiaryAccountId: 'ACC0161',
    relatedTxnUtr: 'TXN002768',
    riskLevel: 'MEDIUM',
    status: 'resolved',
    analystNotes: 'Complaint CMP0008: Transaction verified with merchant gateway logs. Dispute resolved.',
  },
  {
    id: 'CMP0009',
    complaintRef: 'NCRP-CMP0009',
    date: '01 Oct 2026, 13:47 IST',
    shortDescription: 'Syndicate convergence victim; ₹14,065 routed to mule ACC0131 forwarding to hub ACC0140.',
    category: 'Complaint Convergence / Syndicate',
    disputeAmount: 14065.59,
    relatedAccountId: 'ACC0121',
    relatedAccountUpi: 'meera.nair121@synhdfc',
    relatedBeneficiaryUpi: 'rohan.singh131@synicici',
    relatedBeneficiaryAccountId: 'ACC0131',
    relatedTxnUtr: 'TXN002821',
    riskLevel: 'CRITICAL',
    status: 'under_investigation',
    analystNotes: 'Complaint CMP0009: Inflow from HDFC victim forwarded to aggregator spine within 52 seconds.',
  },
  {
    id: 'CMP0010',
    complaintRef: 'NCRP-CMP0010',
    date: '01 Oct 2026, 16:11 IST',
    shortDescription: 'Syndicate convergence victim; ₹10,889 routed to mule ACC0134 forwarding to hub ACC0140.',
    category: 'Complaint Convergence / Syndicate',
    disputeAmount: 10889.77,
    relatedAccountId: 'ACC0124',
    relatedAccountUpi: 'meera.das124@synaxis',
    relatedBeneficiaryUpi: 'rohan.gupta134@synhdfc',
    relatedBeneficiaryAccountId: 'ACC0134',
    relatedTxnUtr: 'TXN002841',
    riskLevel: 'CRITICAL',
    status: 'under_investigation',
    analystNotes: 'Complaint CMP0010: Fifth converging complaint identifying Diya Das (ACC0140) as syndicate cashout head.',
  },
  {
    id: 'CMP-2026-8812',
    complaintRef: 'NCRP-2026-8812',
    date: '15 Oct 2026, 10:14 IST',
    shortDescription: 'Fake utility bill APK scam; unauthorized high-value debit draining victim savings to primary mule.',
    category: 'Extortion / Malicious APK Scam',
    disputeAmount: 480000,
    relatedAccountId: 'ACC_VICTIM_1',
    relatedAccountUpi: 'anand.verma@okaxis',
    relatedBeneficiaryUpi: 'rohit.sharma@paytm',
    relatedTxnUtr: 'UTR20261015998012',
    riskLevel: 'CRITICAL',
    status: 'under_investigation',
    analystNotes: 'Initial victim drain verified via bank gateway logs. 97.5% of funds subsequently structured across 3 mules.',
  },
  {
    id: 'CMP-2026-8815',
    complaintRef: 'NCRP-2026-8815',
    date: '15 Oct 2026, 10:45 IST',
    shortDescription: 'Disputed QR payment reported by ICICI cardholder for unauthorized terminal charge.',
    category: 'Unauthorized UPI Debit',
    disputeAmount: 120000,
    relatedAccountId: 'ACC_MULE_2',
    relatedAccountUpi: 'karan.singh@icici',
    relatedBeneficiaryUpi: 'MERCH_CASHOUT',
    relatedTxnUtr: 'UTR20261015998110',
    riskLevel: 'HIGH',
    status: 'pending_review',
    analystNotes: 'Cardholder claims device was not in locality. Terminal CCTV requested from merchant.',
  },
  {
    id: 'CMP-2026-8790',
    complaintRef: 'NCRP-2026-8790',
    date: '14 Oct 2026, 16:20 IST',
    shortDescription: 'Phishing reward SMS claim verified and funds recovered via bank lien before withdrawal.',
    category: 'Phishing Reward Link',
    disputeAmount: 42000,
    relatedAccountId: 'ACC_LEGIT_1',
    relatedAccountUpi: 'priya.nair@okhdfc',
    relatedBeneficiaryUpi: 'rohit.sharma@paytm',
    relatedTxnUtr: 'UTR20261014110488',
    riskLevel: 'MEDIUM',
    status: 'resolved',
    analystNotes: 'Chargeback approved and settled back to originator account. Case closed by compliance officer.',
  },
  {
    id: 'CMP-2026-8820',
    complaintRef: 'NCRP-2026-8820',
    date: '15 Oct 2026, 11:05 IST',
    shortDescription: 'Telegram investment task scam; multiple structured UPI deposits funneled to Kotak mule.',
    category: 'Investment Fraud',
    disputeAmount: 115000,
    relatedAccountId: 'ACC_MULE_3',
    relatedAccountUpi: 'deepak.gupta@kotak',
    relatedBeneficiaryUpi: 'MERCH_CASHOUT',
    relatedTxnUtr: 'UTR20261015998124',
    riskLevel: 'HIGH',
    status: 'under_investigation',
    analystNotes: 'Account deepak.gupta@kotak flagged in 2 additional cybercrime portal reports across states.',
  }
];

// Chronological fraud timeline sequence derived from graph data
export const SYNTHETIC_TIMELINE: TimelineEvent[] = [
  {
    id: 'TL-1',
    timestamp: '10:02 AM',
    title: 'Initial Victim Account Drain',
    eventType: 'FLAGGED_TRANSACTION',
    sender: 'ACC_VICTIM_1',
    senderName: 'Anand Verma (Victim)',
    senderUpi: 'anand.verma@okaxis',
    receiver: 'ACC_PRIMARY_MULE',
    receiverName: 'Rohit Sharma (Aggregator Mule)',
    receiverUpi: 'rohit.sharma@paytm',
    amount: 480000,
    utr: 'UTR20261015998012',
    edgeId: 'E_TXN_01',
    isFlagged: true,
    explanation: 'An initial high-value anomalous UPI transfer of ₹4,80,000 is debited from the victim account to the primary aggregator mule.',
  },
  {
    id: 'TL-2',
    timestamp: '10:04 AM',
    title: 'Rapid Dispersion Hop 1',
    eventType: 'SUSPICIOUS_PATTERN',
    sender: 'ACC_PRIMARY_MULE',
    senderName: 'Rohit Sharma',
    senderUpi: 'rohit.sharma@paytm',
    receiver: 'ACC_MULE_2',
    receiverName: 'Karan Singh (Mule 1)',
    receiverUpi: 'karan.singh@icici',
    amount: 120000,
    utr: 'UTR20261015998045',
    timeDeltaSeconds: 128,
    edgeId: 'E_TXN_02',
    isFlagged: true,
    explanation: 'The primary receiving account disperses ₹1,20,000 to an intermediary mule within 2 minutes of receipt.',
  },
  {
    id: 'TL-3',
    timestamp: '10:05 AM',
    title: 'Parallel Structuring Split A',
    eventType: 'SUSPICIOUS_PATTERN',
    sender: 'ACC_PRIMARY_MULE',
    senderName: 'Rohit Sharma',
    senderUpi: 'rohit.sharma@paytm',
    receiver: 'ACC_MULE_3',
    receiverName: 'Deepak Gupta (Mule 2)',
    receiverUpi: 'deepak.gupta@kotak',
    amount: 115000,
    utr: 'UTR20261015998059',
    timeDeltaSeconds: 43,
    edgeId: 'E_TXN_03',
    isFlagged: true,
    explanation: 'Funds split into a second parallel mule branch to keep single-hop amounts below ₹2,00,000 velocity triggers.',
  },
  {
    id: 'TL-4',
    timestamp: '10:05 AM',
    title: 'Parallel Structuring Split B',
    eventType: 'SUSPICIOUS_PATTERN',
    sender: 'ACC_PRIMARY_MULE',
    senderName: 'Rohit Sharma',
    senderUpi: 'rohit.sharma@paytm',
    receiver: 'ACC_MULE_4',
    receiverName: 'Amit Patel (Mule 3)',
    receiverUpi: 'amit.patel@oksbi',
    amount: 125000,
    utr: 'UTR20261015998071',
    timeDeltaSeconds: 42,
    edgeId: 'E_TXN_04',
    isFlagged: true,
    explanation: 'Third parallel hop completed. Over 75% of initial victim funds are successfully layered across 3 distinct banks in 213 seconds.',
  },
  {
    id: 'TL-5',
    timestamp: '10:08 AM',
    title: 'Cashout Convergence Hop 1',
    eventType: 'CASHOUT',
    sender: 'ACC_MULE_2',
    senderName: 'Karan Singh',
    senderUpi: 'karan.singh@icici',
    receiver: 'MERCH_CASHOUT',
    receiverName: 'Kishan Electronics & Gold QR',
    receiverUpi: 'MERCH_CASHOUT',
    amount: 118500,
    utr: 'UTR20261015998110',
    timeDeltaSeconds: 148,
    edgeId: 'E_TXN_05',
    isFlagged: true,
    explanation: 'First secondary mule transfers ₹1,18,500 to a commercial merchant QR point to purchase bullion / electronics.',
  },
  {
    id: 'TL-6',
    timestamp: '10:09 AM',
    title: 'Cashout Convergence Hop 2',
    eventType: 'CASHOUT',
    sender: 'ACC_MULE_3',
    senderName: 'Deepak Gupta',
    senderUpi: 'deepak.gupta@kotak',
    receiver: 'MERCH_CASHOUT',
    receiverName: 'Kishan Electronics & Gold QR',
    receiverUpi: 'MERCH_CASHOUT',
    amount: 114000,
    utr: 'UTR20261015998124',
    timeDeltaSeconds: 53,
    edgeId: 'E_TXN_06',
    isFlagged: true,
    explanation: 'Second mule converges at the exact same merchant terminal within 53 seconds, confirming syndicate coordination.',
  },
  {
    id: 'TL-7',
    timestamp: '10:09 AM',
    title: 'Cashout Convergence Hop 3',
    eventType: 'CASHOUT',
    sender: 'ACC_MULE_4',
    senderName: 'Amit Patel',
    senderUpi: 'amit.patel@oksbi',
    receiver: 'MERCH_CASHOUT',
    receiverName: 'Kishan Electronics & Gold QR',
    receiverUpi: 'MERCH_CASHOUT',
    amount: 123000,
    utr: 'UTR20261015998139',
    timeDeltaSeconds: 50,
    edgeId: 'E_TXN_07',
    isFlagged: true,
    explanation: 'Final mule cashout transaction completed. Net funneled volume at merchant reaches ₹3,55,500.',
  },
  {
    id: 'TL-8',
    timestamp: '10:15 AM',
    title: 'Analyst Review & Device Farm Detection',
    eventType: 'ANALYST_REVIEW',
    sender: 'DEV_FARM_1',
    senderName: 'Hardware Identifier DEV-IMEI-889021-X9',
    senderUpi: 'DEV-IMEI-889021-X9',
    receiver: 'ACC_PRIMARY_MULE',
    receiverName: 'Multi-VPA Collusion',
    receiverUpi: 'rohit.sharma@paytm',
    amount: 0,
    utr: 'BIND_889021_ALL',
    isFlagged: true,
    explanation: 'Automated forensic audit links all 4 mule VPAs to 1 physical OnePlus phone; investigator initiates administrative lien review.',
  }
];

export const SYNTHETIC_ALERTS: SuspiciousAlert[] = [
  {
    id: 'ALR-0001',
    title: 'Complaint Convergence: 6 Feeder Mules to Collector',
    clusterId: 'CLUSTER_COMPLAINT_CONVERGENCE_ALR-0001',
    severity: 'CRITICAL',
    riskScore: 90,
    patternType: 'MULE_RING',
    totalVolume: 117139,
    involvedEntitiesCount: 6,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected complaint convergence pattern involving 6 accounts (ACC0131, ACC0132, ACC0133, ACC0134...) and 10 transactions.',
    evidence: [
      {
        ruleId: 'COMPLAINT_CONVERGENCE',
        ruleName: 'Complaint Convergence',
        description: 'Rule COMPLAINT_CONVERGENCE triggered with confidence score 90/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '90%',
          'Participating Accounts': 6,
          'Linked Transactions': 10,
          'Primary Node': 'ACC0131',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0131) and review associated transactions.'
  },
  {
    id: 'ALR-0002',
    title: 'Rapid Onward Transfer: ACC0132 → ACC0140',
    clusterId: 'CLUSTER_RAPID_ONWARD_TRANSFER_ALR-0002',
    severity: 'HIGH',
    riskScore: 89,
    patternType: 'RAPID_DISPERSION',
    totalVolume: 23966,
    involvedEntitiesCount: 2,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected rapid onward transfer pattern involving 2 accounts (ACC0132, ACC0140) and 2 transactions.',
    evidence: [
      {
        ruleId: 'RAPID_ONWARD_TRANSFER',
        ruleName: 'Rapid Onward Transfer',
        description: 'Rule RAPID_ONWARD_TRANSFER triggered with confidence score 89/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '89%',
          'Participating Accounts': 2,
          'Linked Transactions': 2,
          'Primary Node': 'ACC0132',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0132) and review associated transactions.'
  },
  {
    id: 'ALR-0003',
    title: 'Transaction Cycle: Closed Loop (3 Nodes)',
    clusterId: 'CLUSTER_TRANSACTION_CYCLE_ALR-0003',
    severity: 'HIGH',
    riskScore: 85,
    patternType: 'CIRCULAR_ROUTING',
    totalVolume: 74252,
    involvedEntitiesCount: 3,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected transaction cycle pattern involving 3 accounts (ACC0101, ACC0102, ACC0103) and 3 transactions.',
    evidence: [
      {
        ruleId: 'TRANSACTION_CYCLE',
        ruleName: 'Transaction Cycle',
        description: 'Rule TRANSACTION_CYCLE triggered with confidence score 85/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '85%',
          'Participating Accounts': 3,
          'Linked Transactions': 3,
          'Primary Node': 'ACC0101',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0101) and review associated transactions.'
  },
  {
    id: 'ALR-0004',
    title: 'Rapid Onward Transfer: ACC0102 → ACC0103',
    clusterId: 'CLUSTER_RAPID_ONWARD_TRANSFER_ALR-0004',
    severity: 'HIGH',
    riskScore: 82,
    patternType: 'RAPID_DISPERSION',
    totalVolume: 49750,
    involvedEntitiesCount: 2,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected rapid onward transfer pattern involving 2 accounts (ACC0102, ACC0103) and 2 transactions.',
    evidence: [
      {
        ruleId: 'RAPID_ONWARD_TRANSFER',
        ruleName: 'Rapid Onward Transfer',
        description: 'Rule RAPID_ONWARD_TRANSFER triggered with confidence score 82/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '82%',
          'Participating Accounts': 2,
          'Linked Transactions': 2,
          'Primary Node': 'ACC0102',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0102) and review associated transactions.'
  },
  {
    id: 'ALR-0005',
    title: 'Rapid Onward Transfer: ACC0014 → ACC0174',
    clusterId: 'CLUSTER_RAPID_ONWARD_TRANSFER_ALR-0005',
    severity: 'HIGH',
    riskScore: 81,
    patternType: 'RAPID_DISPERSION',
    totalVolume: 6615,
    involvedEntitiesCount: 2,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected rapid onward transfer pattern involving 2 accounts (ACC0014, ACC0174) and 2 transactions.',
    evidence: [
      {
        ruleId: 'RAPID_ONWARD_TRANSFER',
        ruleName: 'Rapid Onward Transfer',
        description: 'Rule RAPID_ONWARD_TRANSFER triggered with confidence score 81/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '81%',
          'Participating Accounts': 2,
          'Linked Transactions': 2,
          'Primary Node': 'ACC0014',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0014) and review associated transactions.'
  },
  {
    id: 'ALR-0006',
    title: 'Multi-Source Fan-In: 30 Remitters to ACC0030',
    clusterId: 'CLUSTER_MULTI_SOURCE_FAN_IN_ALR-0006',
    severity: 'HIGH',
    riskScore: 79,
    patternType: 'MULE_RING',
    totalVolume: 59847,
    involvedEntitiesCount: 31,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected multi source fan in pattern involving 31 accounts (ACC0030, ACC0031, ACC0032, ACC0033...) and 30 transactions.',
    evidence: [
      {
        ruleId: 'MULTI_SOURCE_FAN_IN',
        ruleName: 'Multi Source Fan In',
        description: 'Rule MULTI_SOURCE_FAN_IN triggered with confidence score 79/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '79%',
          'Participating Accounts': 31,
          'Linked Transactions': 30,
          'Primary Node': 'ACC0030',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0030) and review associated transactions.'
  },
  {
    id: 'ALR-0007',
    title: 'Complaint Convergence: 7 Feeder Mules to Collector',
    clusterId: 'CLUSTER_COMPLAINT_CONVERGENCE_ALR-0007',
    severity: 'HIGH',
    riskScore: 78,
    patternType: 'MULE_RING',
    totalVolume: 117904,
    involvedEntitiesCount: 7,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected complaint convergence pattern involving 7 accounts (ACC0131, ACC0132, ACC0133, ACC0134...) and 11 transactions.',
    evidence: [
      {
        ruleId: 'COMPLAINT_CONVERGENCE',
        ruleName: 'Complaint Convergence',
        description: 'Rule COMPLAINT_CONVERGENCE triggered with confidence score 78/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '78%',
          'Participating Accounts': 7,
          'Linked Transactions': 11,
          'Primary Node': 'ACC0131',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0131) and review associated transactions.'
  },
  {
    id: 'ALR-0008',
    title: 'Rapid Onward Transfer: ACC0069 → ACC0144',
    clusterId: 'CLUSTER_RAPID_ONWARD_TRANSFER_ALR-0008',
    severity: 'HIGH',
    riskScore: 78,
    patternType: 'RAPID_DISPERSION',
    totalVolume: 4728,
    involvedEntitiesCount: 2,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected rapid onward transfer pattern involving 2 accounts (ACC0069, ACC0144) and 2 transactions.',
    evidence: [
      {
        ruleId: 'RAPID_ONWARD_TRANSFER',
        ruleName: 'Rapid Onward Transfer',
        description: 'Rule RAPID_ONWARD_TRANSFER triggered with confidence score 78/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '78%',
          'Participating Accounts': 2,
          'Linked Transactions': 2,
          'Primary Node': 'ACC0069',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0069) and review associated transactions.'
  },
  {
    id: 'ALR-0009',
    title: 'Rapid Onward Transfer: ACC0013 → ACC0014',
    clusterId: 'CLUSTER_RAPID_ONWARD_TRANSFER_ALR-0009',
    severity: 'HIGH',
    riskScore: 77,
    patternType: 'RAPID_DISPERSION',
    totalVolume: 88920,
    involvedEntitiesCount: 2,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected rapid onward transfer pattern involving 2 accounts (ACC0013, ACC0014) and 2 transactions.',
    evidence: [
      {
        ruleId: 'RAPID_ONWARD_TRANSFER',
        ruleName: 'Rapid Onward Transfer',
        description: 'Rule RAPID_ONWARD_TRANSFER triggered with confidence score 77/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '77%',
          'Participating Accounts': 2,
          'Linked Transactions': 2,
          'Primary Node': 'ACC0013',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0013) and review associated transactions.'
  },
  {
    id: 'ALR-0010',
    title: 'Rapid Onward Transfer: ACC0131 → ACC0140',
    clusterId: 'CLUSTER_RAPID_ONWARD_TRANSFER_ALR-0010',
    severity: 'HIGH',
    riskScore: 77,
    patternType: 'RAPID_DISPERSION',
    totalVolume: 27287,
    involvedEntitiesCount: 2,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected rapid onward transfer pattern involving 2 accounts (ACC0131, ACC0140) and 2 transactions.',
    evidence: [
      {
        ruleId: 'RAPID_ONWARD_TRANSFER',
        ruleName: 'Rapid Onward Transfer',
        description: 'Rule RAPID_ONWARD_TRANSFER triggered with confidence score 77/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '77%',
          'Participating Accounts': 2,
          'Linked Transactions': 2,
          'Primary Node': 'ACC0131',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0131) and review associated transactions.'
  },
  {
    id: 'ALR-0011',
    title: 'Rapid Onward Transfer: ACC0012 → ACC0013',
    clusterId: 'CLUSTER_RAPID_ONWARD_TRANSFER_ALR-0011',
    severity: 'HIGH',
    riskScore: 75,
    patternType: 'RAPID_DISPERSION',
    totalVolume: 93600,
    involvedEntitiesCount: 2,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected rapid onward transfer pattern involving 2 accounts (ACC0012, ACC0013) and 2 transactions.',
    evidence: [
      {
        ruleId: 'RAPID_ONWARD_TRANSFER',
        ruleName: 'Rapid Onward Transfer',
        description: 'Rule RAPID_ONWARD_TRANSFER triggered with confidence score 75/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '75%',
          'Participating Accounts': 2,
          'Linked Transactions': 2,
          'Primary Node': 'ACC0012',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0012) and review associated transactions.'
  },
  {
    id: 'ALR-0012',
    title: 'Rapid Onward Transfer: ACC0134 → ACC0140',
    clusterId: 'CLUSTER_RAPID_ONWARD_TRANSFER_ALR-0012',
    severity: 'MEDIUM',
    riskScore: 71,
    patternType: 'RAPID_DISPERSION',
    totalVolume: 21126,
    involvedEntitiesCount: 2,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected rapid onward transfer pattern involving 2 accounts (ACC0134, ACC0140) and 2 transactions.',
    evidence: [
      {
        ruleId: 'RAPID_ONWARD_TRANSFER',
        ruleName: 'Rapid Onward Transfer',
        description: 'Rule RAPID_ONWARD_TRANSFER triggered with confidence score 71/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '71%',
          'Participating Accounts': 2,
          'Linked Transactions': 2,
          'Primary Node': 'ACC0134',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0134) and review associated transactions.'
  },
  {
    id: 'ALR-0013',
    title: 'Complaint Convergence: 2 Feeder Mules to Collector',
    clusterId: 'CLUSTER_COMPLAINT_CONVERGENCE_ALR-0013',
    severity: 'MEDIUM',
    riskScore: 56,
    patternType: 'MULE_RING',
    totalVolume: 3817,
    involvedEntitiesCount: 2,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected complaint convergence pattern involving 2 accounts (ACC0163, ACC0165) and 3 transactions.',
    evidence: [
      {
        ruleId: 'COMPLAINT_CONVERGENCE',
        ruleName: 'Complaint Convergence',
        description: 'Rule COMPLAINT_CONVERGENCE triggered with confidence score 56/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '56%',
          'Participating Accounts': 2,
          'Linked Transactions': 3,
          'Primary Node': 'ACC0163',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0163) and review associated transactions.'
  },
  {
    id: 'ALR-0014',
    title: 'Multi-Source Fan-In: 8 Remitters to ACC0170',
    clusterId: 'CLUSTER_MULTI_SOURCE_FAN_IN_ALR-0014',
    severity: 'MEDIUM',
    riskScore: 51,
    patternType: 'MULE_RING',
    totalVolume: 34622,
    involvedEntitiesCount: 9,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected multi source fan in pattern involving 9 accounts (ACC0170, ACC0171, ACC0172, ACC0173...) and 8 transactions.',
    evidence: [
      {
        ruleId: 'MULTI_SOURCE_FAN_IN',
        ruleName: 'Multi Source Fan In',
        description: 'Rule MULTI_SOURCE_FAN_IN triggered with confidence score 51/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '51%',
          'Participating Accounts': 9,
          'Linked Transactions': 8,
          'Primary Node': 'ACC0170',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0170) and review associated transactions.'
  },
  {
    id: 'ALR-0015',
    title: 'Complaint Convergence: 5 Feeder Mules to Collector',
    clusterId: 'CLUSTER_COMPLAINT_CONVERGENCE_ALR-0015',
    severity: 'MEDIUM',
    riskScore: 50,
    patternType: 'MULE_RING',
    totalVolume: 72173,
    involvedEntitiesCount: 5,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected complaint convergence pattern involving 5 accounts (ACC0049, ACC0131, ACC0133, ACC0135...) and 7 transactions.',
    evidence: [
      {
        ruleId: 'COMPLAINT_CONVERGENCE',
        ruleName: 'Complaint Convergence',
        description: 'Rule COMPLAINT_CONVERGENCE triggered with confidence score 50/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '50%',
          'Participating Accounts': 5,
          'Linked Transactions': 7,
          'Primary Node': 'ACC0049',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0049) and review associated transactions.'
  },
  {
    id: 'ALR-0016',
    title: 'Shared Device Collusion: Hardware Cluster (3 Accounts)',
    clusterId: 'CLUSTER_SHARED_DEVICE_ALR-0016',
    severity: 'LOW',
    riskScore: 20,
    patternType: 'DEVICE_FARM',
    totalVolume: 21936,
    involvedEntitiesCount: 3,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected shared device pattern involving 3 accounts (ACC0019, ACC0069, ACC0080) and 28 transactions.',
    evidence: [
      {
        ruleId: 'SHARED_DEVICE',
        ruleName: 'Shared Device',
        description: 'Rule SHARED_DEVICE triggered with confidence score 20/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '20%',
          'Participating Accounts': 3,
          'Linked Transactions': 28,
          'Primary Node': 'ACC0019',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0019) and review associated transactions.'
  },
  {
    id: 'ALR-0017',
    title: 'Shared Device Collusion: Hardware Cluster (3 Accounts)',
    clusterId: 'CLUSTER_SHARED_DEVICE_ALR-0017',
    severity: 'LOW',
    riskScore: 20,
    patternType: 'DEVICE_FARM',
    totalVolume: 88197,
    involvedEntitiesCount: 3,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected shared device pattern involving 3 accounts (ACC0035, ACC0101, ACC0200) and 72 transactions.',
    evidence: [
      {
        ruleId: 'SHARED_DEVICE',
        ruleName: 'Shared Device',
        description: 'Rule SHARED_DEVICE triggered with confidence score 20/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '20%',
          'Participating Accounts': 3,
          'Linked Transactions': 72,
          'Primary Node': 'ACC0035',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0035) and review associated transactions.'
  },
  {
    id: 'ALR-0018',
    title: 'Shared Device Collusion: Hardware Cluster (3 Accounts)',
    clusterId: 'CLUSTER_SHARED_DEVICE_ALR-0018',
    severity: 'LOW',
    riskScore: 20,
    patternType: 'DEVICE_FARM',
    totalVolume: 7869,
    involvedEntitiesCount: 3,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected shared device pattern involving 3 accounts (ACC0054, ACC0084, ACC0190) and 15 transactions.',
    evidence: [
      {
        ruleId: 'SHARED_DEVICE',
        ruleName: 'Shared Device',
        description: 'Rule SHARED_DEVICE triggered with confidence score 20/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '20%',
          'Participating Accounts': 3,
          'Linked Transactions': 15,
          'Primary Node': 'ACC0054',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0054) and review associated transactions.'
  },
  {
    id: 'ALR-0019',
    title: 'Shared Device Collusion: Hardware Cluster (3 Accounts)',
    clusterId: 'CLUSTER_SHARED_DEVICE_ALR-0019',
    severity: 'LOW',
    riskScore: 20,
    patternType: 'DEVICE_FARM',
    totalVolume: 67863,
    involvedEntitiesCount: 3,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected shared device pattern involving 3 accounts (ACC0087, ACC0102, ACC0142) and 66 transactions.',
    evidence: [
      {
        ruleId: 'SHARED_DEVICE',
        ruleName: 'Shared Device',
        description: 'Rule SHARED_DEVICE triggered with confidence score 20/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '20%',
          'Participating Accounts': 3,
          'Linked Transactions': 66,
          'Primary Node': 'ACC0087',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0087) and review associated transactions.'
  },
  {
    id: 'ALR-0020',
    title: 'Shared Device Collusion: Hardware Cluster (3 Accounts)',
    clusterId: 'CLUSTER_SHARED_DEVICE_ALR-0020',
    severity: 'LOW',
    riskScore: 20,
    patternType: 'DEVICE_FARM',
    totalVolume: 64896,
    involvedEntitiesCount: 3,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected shared device pattern involving 3 accounts (ACC0094, ACC0124, ACC0140) and 91 transactions.',
    evidence: [
      {
        ruleId: 'SHARED_DEVICE',
        ruleName: 'Shared Device',
        description: 'Rule SHARED_DEVICE triggered with confidence score 20/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '20%',
          'Participating Accounts': 3,
          'Linked Transactions': 91,
          'Primary Node': 'ACC0094',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0094) and review associated transactions.'
  },
  {
    id: 'ALR-0021',
    title: 'Shared Device Collusion: Hardware Cluster (3 Accounts)',
    clusterId: 'CLUSTER_SHARED_DEVICE_ALR-0021',
    severity: 'LOW',
    riskScore: 20,
    patternType: 'DEVICE_FARM',
    totalVolume: 41071,
    involvedEntitiesCount: 3,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected shared device pattern involving 3 accounts (ACC0118, ACC0120, ACC0196) and 65 transactions.',
    evidence: [
      {
        ruleId: 'SHARED_DEVICE',
        ruleName: 'Shared Device',
        description: 'Rule SHARED_DEVICE triggered with confidence score 20/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '20%',
          'Participating Accounts': 3,
          'Linked Transactions': 65,
          'Primary Node': 'ACC0118',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0118) and review associated transactions.'
  },
  {
    id: 'ALR-0022',
    title: 'Shared Device Collusion: Hardware Cluster (3 Accounts)',
    clusterId: 'CLUSTER_SHARED_DEVICE_ALR-0022',
    severity: 'LOW',
    riskScore: 20,
    patternType: 'DEVICE_FARM',
    totalVolume: 64394,
    involvedEntitiesCount: 3,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected shared device pattern involving 3 accounts (ACC0139, ACC0144, ACC0182) and 104 transactions.',
    evidence: [
      {
        ruleId: 'SHARED_DEVICE',
        ruleName: 'Shared Device',
        description: 'Rule SHARED_DEVICE triggered with confidence score 20/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '20%',
          'Participating Accounts': 3,
          'Linked Transactions': 104,
          'Primary Node': 'ACC0139',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0139) and review associated transactions.'
  },
  {
    id: 'ALR-0023',
    title: 'Shared Device Collusion: Hardware Cluster (8 Accounts)',
    clusterId: 'CLUSTER_SHARED_DEVICE_ALR-0023',
    severity: 'LOW',
    riskScore: 20,
    patternType: 'DEVICE_FARM',
    totalVolume: 34622,
    involvedEntitiesCount: 8,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected shared device pattern involving 8 accounts (ACC0171, ACC0172, ACC0173, ACC0174...) and 8 transactions.',
    evidence: [
      {
        ruleId: 'SHARED_DEVICE',
        ruleName: 'Shared Device',
        description: 'Rule SHARED_DEVICE triggered with confidence score 20/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '20%',
          'Participating Accounts': 8,
          'Linked Transactions': 8,
          'Primary Node': 'ACC0171',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0171) and review associated transactions.'
  },
  {
    id: 'ALR-0024',
    title: 'Shared Device Collusion: Hardware Cluster (5 Accounts)',
    clusterId: 'CLUSTER_SHARED_DEVICE_ALR-0024',
    severity: 'LOW',
    riskScore: 20,
    patternType: 'DEVICE_FARM',
    totalVolume: 18103,
    involvedEntitiesCount: 5,
    detectedAt: '2026-10-15 22:47:50 IST',
    summary: 'Detected shared device pattern involving 5 accounts (ACC0181, ACC0182, ACC0183, ACC0184...) and 30 transactions.',
    evidence: [
      {
        ruleId: 'SHARED_DEVICE',
        ruleName: 'Shared Device',
        description: 'Rule SHARED_DEVICE triggered with confidence score 20/100 based on synthetic bank and gateway records.',
        metrics: {
          'Confidence Score': '20%',
          'Participating Accounts': 5,
          'Linked Transactions': 30,
          'Primary Node': 'ACC0181',
        }
      }
    ],
    suggestedAction: 'Initiate supervisory audit on primary node (ACC0181) and review associated transactions.'
  },
  {
    id: 'ALT_2026_094',
    title: 'High-Velocity Structured Mule Ring & Shared Device Farm',
    clusterId: 'CLUSTER_ALPHA_CHAKRAVYUH',
    severity: 'CRITICAL',
    riskScore: 96,
    patternType: 'MULE_RING',
    totalVolume: 480000,
    involvedEntitiesCount: 7,
    detectedAt: '2026-10-15 10:12:00 IST',
    summary: '₹4,80,000 received from victim account within 2 mins and immediately structured into 3 parallel mule hops, converging at an electronics merchant QR. All 4 beneficiary VPAs share 1 rooted physical device.',
    evidence: [
      {
        ruleId: 'R-101',
        ruleName: 'Rapid Dispersion Velocity (< 5 Mins)',
        description: '97.5% of incoming funds dispersed across 3 external accounts within 213 seconds.',
        metrics: { 'Inflow (₹)': 480000, 'Dispersed (₹)': 360000, 'Hop Latency': '3m 33s' }
      },
      {
        ruleId: 'R-204',
        ruleName: 'Shared Device Hardware Identifier Abuse',
        description: 'Device DEV-IMEI-889021-X9 bound to 4 different user names across 3 distinct banking apps.',
        metrics: { 'Associated VPAs': 4, 'Root Flags Detected': 1, 'Distinct KYC Names': 4 }
      },
      {
        ruleId: 'R-309',
        ruleName: 'Cashout Funnel Convergence',
        description: 'All 3 secondary mule nodes settled funds at Merchant QR (MID-99042) within 150 seconds of each other.',
        metrics: { 'Funneled Volume (₹)': 355500, 'Merchant Category': 'Bullion / Electronics' }
      }
    ],
    suggestedAction: 'Immediate temporary lien freeze on 4 mule VPAs and blacklist hardware identifier DEV-IMEI-889021-X9.'
  },
  {
    id: 'ALT_2026_088',
    title: 'Circular Layering Syndicate (Potential Smurfing)',
    clusterId: 'CLUSTER_BETA_CYCLING',
    severity: 'HIGH',
    riskScore: 88,
    patternType: 'CIRCULAR_ROUTING',
    totalVolume: 240000,
    involvedEntitiesCount: 5,
    detectedAt: '2026-10-15 09:45:00 IST',
    summary: 'Closed-loop cyclic transactions detected across 4 bank accounts returning 92% of original principal to the originator minus 8% transaction commision.',
    evidence: [
      {
        ruleId: 'R-401',
        ruleName: 'Graph Cycle Detection (NetworkX DiGraph)',
        description: 'Directed cycle identified: ACC_A -> ACC_B -> ACC_C -> ACC_D -> ACC_A.',
        metrics: { 'Cycle Length': 4, 'Leakage Rate': '8.2%', 'Net Cycle Time': '18m 10s' }
      }
    ],
    suggestedAction: 'Escalate to Anti-Money Laundering (AML) supervisory queue for UTR-level KYC verification.'
  },
  {
    id: 'ALT_2026_067',
    title: 'Off-Hours High Velocity Merchant Inflow',
    clusterId: 'CLUSTER_GAMMA_MERCH',
    severity: 'MEDIUM',
    riskScore: 67,
    patternType: 'RAPID_DISPERSION',
    totalVolume: 125000,
    involvedEntitiesCount: 3,
    detectedAt: '2026-10-15 03:22:15 IST',
    summary: 'Unusual spike of 15 micro-transactions (₹8,000 - ₹9,900) processed between 02:30 AM and 03:30 AM on a small grocery QR.',
    evidence: [
      {
        ruleId: 'R-502',
        ruleName: 'Temporal Anomaly & Structuring Threshold',
        description: 'All transactions clustered immediately below the ₹10,000 SMS verification trigger threshold.',
        metrics: { 'Avg Txn (₹)': 8333, 'Hours Window': '02:00 - 04:00' }
      }
    ],
    suggestedAction: 'Request merchant settlement hold pending terminal verification.'
  }
];

export const SYNTHETIC_CASES: CaseFile[] = [
  {
    id: 'CASE-S07-CONVERGE',
    title: 'Operation Chakravyuh: S07 Complaint Convergence Syndicate',
    analyst: 'Bharath (Lead Backend & Detection Engine Owner)',
    status: 'IN_REVIEW',
    priority: 'CRITICAL',
    createdAt: '2026-10-15 10:15 IST',
    flaggedVolume: 60380,
    primaryClusterId: 'CLUSTER_S07_CONVERGENCE',
    notes: [
      {
        id: 'N-S07-1',
        author: 'Investigator Priya',
        timestamp: '10:20 IST',
        text: '5 victim complaints (CMP0004, CMP0006, CMP0007, CMP0009, CMP0010) show identical onward transfer behavior converging at Collector Diya Das (ACC0140).'
      },
      {
        id: 'N-S07-2',
        author: 'Bharath',
        timestamp: '10:35 IST',
        text: 'Primary mule Vikram Reddy (ACC0135) received ₹10,732.62 from victim ACC0125 and forwarded 94% within 58 seconds. Full network exhibits 100% layering rate.'
      }
    ]
  },
  {
    id: 'CASE-S01-RAPID',
    title: 'S01 Rapid Transfer: 3-Hop Low-Latency Chain',
    analyst: 'Bharath (Lead Backend & Detection Engine Owner)',
    status: 'IN_REVIEW',
    priority: 'HIGH',
    createdAt: '2026-10-15 09:30 IST',
    flaggedVolume: 35000,
    primaryClusterId: 'CLUSTER_S01_RAPID_CHAIN',
    notes: [
      {
        id: 'N-S01-1',
        author: 'Bharath',
        timestamp: '09:40 IST',
        text: 'Funds transferred ACC0011 -> ACC0012 -> ACC0013 -> ACC0014 in under 6 minutes with 95% pass-through at each hop.'
      }
    ]
  },
  {
    id: 'CASE-S03-FANIN',
    title: 'S03 Fan-In: Multi-Source Micro-Deposit Smurfing',
    analyst: 'Devika (Financial Crimes Desk)',
    status: 'OPEN',
    priority: 'HIGH',
    createdAt: '2026-10-15 08:45 IST',
    flaggedVolume: 60000,
    primaryClusterId: 'CLUSTER_S03_FANIN',
    notes: [
      {
        id: 'N-S03-1',
        author: 'Devika',
        timestamp: '09:00 IST',
        text: '30 individual sender accounts credited ACC0030 with ~₹2,000 each in 3 hours. Suspected recruitment mule.'
      }
    ]
  },
  {
    id: 'CASE-S05-CYCLE',
    title: 'S05 Cycle: Closed Triangular Layering Ring',
    analyst: 'Bharath (Lead Backend & Detection Engine Owner)',
    status: 'IN_REVIEW',
    priority: 'HIGH',
    createdAt: '2026-10-15 07:15 IST',
    flaggedVolume: 25000,
    primaryClusterId: 'CLUSTER_S05_CYCLE',
    notes: [
      {
        id: 'N-S05-1',
        author: 'Bharath',
        timestamp: '07:30 IST',
        text: 'Directed loop ACC0101 -> ACC0102 -> ACC0103 -> ACC0101 detected by NetworkX simple_cycles algorithm with 98% principal retention.'
      }
    ]
  },
  {
    id: 'CASE-S09-DEVICE',
    title: 'S09 Hardware Collusion: Rooted Device Farm',
    analyst: 'Investigator Priya',
    status: 'OPEN',
    priority: 'HIGH',
    createdAt: '2026-10-15 03:00 IST',
    flaggedVolume: 34200,
    primaryClusterId: 'CLUSTER_S09_SHARED_DEVICE',
    notes: [
      {
        id: 'N-S09-1',
        author: 'Investigator Priya',
        timestamp: '03:15 IST',
        text: 'Device DEV9001 logged 8 distinct user identities sending nocturnal transfers to ACC0170.'
      }
    ]
  },
  {
    id: 'CASE-2026-0041',
    title: 'Operation Chakravyuh: Structured UPI Mule Ring',
    analyst: 'Bharath (Lead Backend & Forensics)',
    status: 'IN_REVIEW',
    priority: 'CRITICAL',
    createdAt: '2026-10-15 10:15 IST',
    flaggedVolume: 480000,
    primaryClusterId: 'CLUSTER_ALPHA_CHAKRAVYUH',
    notes: [
      {
        id: 'N-1',
        author: 'Investigator Priya',
        timestamp: '10:20 IST',
        text: 'NCRP complaint confirmed. Victim was lured into fake courier package customs scam. Funds drained via UPI.'
      },
      {
        id: 'N-2',
        author: 'Bharath',
        timestamp: '10:32 IST',
        text: 'Device DEV-IMEI-889021-X9 has logged 4 mule identities in the last 48 hours. Recommend lien freeze on Axis/Paytm/Kotak endpoints.'
      }
    ]
  },
  {
    id: 'CASE-2026-0038',
    title: 'Off-Peak Merchant Funneling Assessment',
    analyst: 'Devika (Financial Crimes Desk)',
    status: 'OPEN',
    priority: 'MEDIUM',
    createdAt: '2026-10-15 04:00 IST',
    flaggedVolume: 125000,
    primaryClusterId: 'CLUSTER_GAMMA_MERCH',
    notes: [
      {
        id: 'N-1',
        author: 'Devika',
        timestamp: '04:15 IST',
        text: 'Merchant KYC flagged pending physical premise verification.'
      }
    ]
  }
];
