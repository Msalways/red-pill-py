"use client";

import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, LineChart, Line, AreaChart, Area, Cell } from 'recharts';

interface ChartData {
  x: string | number;
  y: number;
  series?: string | number;
  label_x?: string;
  label_y?: string;
  label_series?: string;
}

interface Metadata {
  chartType: string;
  xAxis: { field: string; label: string };
  yAxis: { field: string; label: string };
  series?: { field: string; label: string };
}

// Generate dates for past 3 months
const generateDates = () => {
  const dates = [];
  const now = new Date();
  for (let i = 0; i < 90; i++) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    dates.push(date.toISOString().split('T')[0]);
  }
  return dates;
};

const dates = generateDates();

const hubspotLikeData = {
  deals: [
    { id: "DL-001", title: "Enterprise Software License", amount: 125000, stage: "closed_won", company: "Acme Corp", owner: "Sarah Chen", created_at: dates[0], closed_at: dates[5], probability: 100 },
    { id: "DL-002", title: "Annual Support Contract", amount: 45000, stage: "closed_won", company: "TechStart Inc", owner: "Mike Johnson", created_at: dates[2], closed_at: dates[8], probability: 100 },
    { id: "DL-003", title: "Cloud Migration Project", amount: 280000, stage: "negotiation", company: "GlobalTech Ltd", owner: "Sarah Chen", created_at: dates[5], closed_at: null, probability: 75 },
    { id: "DL-004", title: "Security Audit Package", amount: 35000, stage: "qualified", company: "FinanceFirst", owner: "Lisa Wang", created_at: dates[10], closed_at: null, probability: 60 },
    { id: "DL-005", title: "Data Analytics Platform", amount: 95000, stage: "proposal", company: "HealthPlus", owner: "Mike Johnson", created_at: dates[15], closed_at: null, probability: 50 },
    { id: "DL-006", title: "CRM Implementation", amount: 175000, stage: "closed_won", company: "RetailMax", owner: "Sarah Chen", created_at: dates[20], closed_at: dates[25], probability: 100 },
    { id: "DL-007", title: "API Integration", amount: 28000, stage: "closed_lost", company: "StartupXYZ", owner: "Lisa Wang", created_at: dates[25], closed_at: dates[30], probability: 0 },
    { id: "DL-008", title: "Mobile App Development", amount: 150000, stage: "discovery", company: "MediaGroup", owner: "Mike Johnson", created_at: dates[30], closed_at: null, probability: 30 },
    { id: "DL-009", title: "Maintenance Agreement", amount: 24000, stage: "closed_won", company: "Acme Corp", owner: "Sarah Chen", created_at: dates[35], closed_at: dates[40], probability: 100 },
    { id: "DL-010", title: "Enterprise Backup Solution", amount: 85000, stage: "qualified", company: "DataSecure Inc", owner: "Lisa Wang", created_at: dates[40], closed_at: null, probability: 70 },
    { id: "DL-011", title: "AI Analytics Add-on", amount: 62000, stage: "proposal", company: "TechStart Inc", owner: "Mike Johnson", created_at: dates[45], closed_at: null, probability: 45 },
    { id: "DL-012", title: "Custom Integration", amount: 48000, stage: "negotiation", company: "RetailMax", owner: "Sarah Chen", created_at: dates[50], closed_at: null, probability: 80 },
    { id: "DL-013", title: "Premium Support Tier", amount: 36000, stage: "closed_won", company: "GlobalTech Ltd", owner: "Lisa Wang", created_at: dates[55], closed_at: dates[60], probability: 100 },
    { id: "DL-014", title: "Infrastructure Upgrade", amount: 320000, stage: "discovery", company: "HealthPlus", owner: "Mike Johnson", created_at: dates[60], closed_at: null, probability: 25 },
    { id: "DL-015", title: "Training Program", amount: 18000, stage: "qualified", company: "FinanceFirst", owner: "Sarah Chen", created_at: dates[65], closed_at: null, probability: 55 },
  ],
  companies: [
    { id: "CO-001", name: "Acme Corp", industry: "Technology", size: "enterprise", revenue: 50000000, country: "USA", owner: "Sarah Chen" },
    { id: "CO-002", name: "TechStart Inc", industry: "SaaS", size: "mid-market", revenue: 5000000, country: "USA", owner: "Mike Johnson" },
    { id: "CO-003", name: "GlobalTech Ltd", industry: "Manufacturing", size: "enterprise", revenue: 100000000, country: "UK", owner: "Sarah Chen" },
    { id: "CO-004", name: "FinanceFirst", industry: "Financial Services", size: "enterprise", revenue: 75000000, country: "USA", owner: "Lisa Wang" },
    { id: "CO-005", name: "HealthPlus", industry: "Healthcare", size: "mid-market", revenue: 15000000, country: "Canada", owner: "Mike Johnson" },
    { id: "CO-006", name: "RetailMax", industry: "Retail", size: "enterprise", revenue: 200000000, country: "USA", owner: "Sarah Chen" },
    { id: "CO-007", name: "StartupXYZ", industry: "Technology", size: "smb", revenue: 500000, country: "USA", owner: "Lisa Wang" },
    { id: "CO-008", name: "MediaGroup", industry: "Media", size: "mid-market", revenue: 8000000, country: "UK", owner: "Mike Johnson" },
    { id: "CO-009", name: "DataSecure Inc", industry: "Cybersecurity", size: "mid-market", revenue: 12000000, country: "USA", owner: "Lisa Wang" },
  ],
  contacts: [
    { id: "CT-001", email: "john.smith@acmecorp.com", firstname: "John", lastname: "Smith", company: "Acme Corp", status: "active", lead_status: "qualified", created_at: dates[1] },
    { id: "CT-002", email: "jane.doe@techstart.io", firstname: "Jane", lastname: "Doe", company: "TechStart Inc", status: "active", lead_status: "open", created_at: dates[5] },
    { id: "CT-003", email: "bob.wilson@globaltech.com", firstname: "Bob", lastname: "Wilson", company: "GlobalTech Ltd", status: "active", lead_status: "qualified", created_at: dates[10] },
    { id: "CT-004", email: "alice@healthplus.ca", firstname: "Alice", lastname: "Johnson", company: "HealthPlus", status: "inactive", lead_status: "lost", created_at: dates[15] },
    { id: "CT-005", email: "charlie.brown@retailmax.com", firstname: "Charlie", lastname: "Brown", company: "RetailMax", status: "active", lead_status: "qualified", created_at: dates[20] },
    { id: "CT-006", email: "david@startupxyz.io", firstname: "David", lastname: "Lee", company: "StartupXYZ", status: "active", lead_status: "open", created_at: dates[25] },
    { id: "CT-007", email: "emma@datasecure.com", firstname: "Emma", lastname: "Davis", company: "DataSecure Inc", status: "active", lead_status: "qualified", created_at: dates[30] },
    { id: "CT-008", email: "frank@mediagroup.co.uk", firstname: "Frank", lastname: "Miller", company: "MediaGroup", status: "active", lead_status: "open", created_at: dates[35] },
  ],
  activities: [
    { id: "AC-001", type: "call", subject: "Discovery Call", contact: "John Smith", deal: "DL-001", owner: "Sarah Chen", timestamp: dates[1], duration: 1800, outcome: "successful" },
    { id: "AC-002", type: "email", subject: "Proposal Sent", contact: "Jane Doe", deal: "DL-002", owner: "Mike Johnson", timestamp: dates[3], duration: null, outcome: "sent" },
    { id: "AC-003", type: "meeting", subject: "Demo Presentation", contact: "Bob Wilson", deal: "DL-003", owner: "Sarah Chen", timestamp: dates[8], duration: 3600, outcome: "completed" },
    { id: "AC-004", type: "call", subject: "Follow-up Call", contact: "Alice Johnson", deal: "DL-004", owner: "Lisa Wang", timestamp: dates[12], duration: 1200, outcome: "successful" },
    { id: "AC-005", type: "email", subject: "Contract Review", contact: "Charlie Brown", deal: "DL-006", owner: "Sarah Chen", timestamp: dates[18], duration: null, outcome: "sent" },
    { id: "AC-006", type: "meeting", subject: "Negotiation", contact: "David Lee", deal: "DL-007", owner: "Lisa Wang", timestamp: dates[22], duration: 2700, outcome: "completed" },
    { id: "AC-007", type: "call", subject: "Security Discussion", contact: "Emma Davis", deal: "DL-010", owner: "Lisa Wang", timestamp: dates[28], duration: 2400, outcome: "successful" },
    { id: "AC-008", type: "email", subject: "Technical Requirements", contact: "Frank Miller", deal: "DL-008", owner: "Mike Johnson", timestamp: dates[33], duration: null, outcome: "sent" },
    { id: "AC-009", type: "meeting", subject: "QBR Meeting", contact: "John Smith", deal: "DL-009", owner: "Sarah Chen", timestamp: dates[38], duration: 5400, outcome: "completed" },
    { id: "AC-010", type: "call", subject: "Upsell Discussion", contact: "Jane Doe", deal: "DL-011", owner: "Mike Johnson", timestamp: dates[42], duration: 1500, outcome: "successful" },
  ],
  owners: [
    { id: "OW-001", name: "Sarah Chen", email: "sarah@company.com", team: "Enterprise", quota: 500000, achieved: 437000 },
    { id: "OW-002", name: "Mike Johnson", email: "mike@company.com", team: "Mid-Market", quota: 300000, achieved: 195000 },
    { id: "OW-003", name: "Lisa Wang", email: "lisa@company.com", team: "SMB", quota: 200000, achieved: 86000 },
  ]
};

const ecommerceData = {
  orders: [
    { id: "ORD-001", customer: "John Smith", email: "john@example.com", product: "Laptop Pro", category: "Electronics", amount: 1299.99, status: "completed", date: dates[1], payment: "credit_card" },
    { id: "ORD-002", customer: "Jane Doe", email: "jane@example.com", product: "Wireless Mouse", category: "Electronics", amount: 49.99, status: "completed", date: dates[3], payment: "paypal" },
    { id: "ORD-003", customer: "Bob Wilson", email: "bob@example.com", product: "Running Shoes", category: "Sports", amount: 129.99, status: "completed", date: dates[5], payment: "credit_card" },
    { id: "ORD-004", customer: "Alice Brown", email: "alice@example.com", product: "Coffee Maker", category: "Home", amount: 89.99, status: "pending", date: dates[8], payment: "credit_card" },
    { id: "ORD-005", customer: "Charlie Davis", email: "charlie@example.com", product: "Laptop Pro", category: "Electronics", amount: 1299.99, status: "completed", date: dates[10], payment: "debit_card" },
    { id: "ORD-006", customer: "Emma Evans", email: "emma@example.com", product: "Yoga Mat", category: "Sports", amount: 34.99, status: "completed", date: dates[12], payment: "credit_card" },
    { id: "ORD-007", customer: "Frank Ford", email: "frank@example.com", product: "Blender", category: "Home", amount: 69.99, status: "cancelled", date: dates[15], payment: "credit_card" },
    { id: "ORD-008", customer: "Grace Green", email: "grace@example.com", product: "Wireless Mouse", category: "Electronics", amount: 49.99, status: "completed", date: dates[18], payment: "paypal" },
    { id: "ORD-009", customer: "Henry Hill", email: "henry@example.com", product: "Dumbbells", category: "Sports", amount: 79.99, status: "completed", date: dates[20], payment: "credit_card" },
    { id: "ORD-010", customer: "Ivy Irwin", email: "ivy@example.com", product: "Toaster", category: "Home", amount: 44.99, status: "completed", date: dates[22], payment: "debit_card" },
    { id: "ORD-011", customer: "Jack Jones", email: "jack@example.com", product: "Laptop Pro", category: "Electronics", amount: 1299.99, status: "refunded", date: dates[25], payment: "credit_card" },
    { id: "ORD-012", customer: "Karen King", email: "karen@example.com", product: "Running Shoes", category: "Sports", amount: 129.99, status: "completed", date: dates[28], payment: "paypal" },
  ],
  products: [
    { id: "PRD-001", name: "Laptop Pro", category: "Electronics", price: 1299.99, stock: 45, supplier: "TechCorp" },
    { id: "PRD-002", name: "Wireless Mouse", category: "Electronics", price: 49.99, stock: 120, supplier: "TechCorp" },
    { id: "PRD-003", name: "Running Shoes", category: "Sports", price: 129.99, stock: 80, supplier: "SportLife" },
    { id: "PRD-004", name: "Yoga Mat", category: "Sports", price: 34.99, stock: 200, supplier: "SportLife" },
    { id: "PRD-005", name: "Coffee Maker", category: "Home", price: 89.99, stock: 60, supplier: "HomeEssentials" },
    { id: "PRD-006", name: "Blender", category: "Home", price: 69.99, stock: 35, supplier: "HomeEssentials" },
    { id: "PRD-007", name: "Dumbbells", category: "Sports", price: 79.99, stock: 90, supplier: "SportLife" },
    { id: "PRD-008", name: "Toaster", category: "Home", price: 44.99, stock: 75, supplier: "HomeEssentials" },
  ],
  customers: [
    { id: "CUS-001", name: "John Smith", email: "john@example.com", tier: "premium", orders: 12, total_spent: 2450.00, country: "USA" },
    { id: "CUS-002", name: "Jane Doe", email: "jane@example.com", tier: "standard", orders: 3, total_spent: 189.99, country: "Canada" },
    { id: "CUS-003", name: "Bob Wilson", email: "bob@example.com", tier: "premium", orders: 8, total_spent: 1560.00, country: "USA" },
    { id: "CUS-004", name: "Alice Brown", email: "alice@example.com", tier: "standard", orders: 2, total_spent: 134.98, country: "UK" },
    { id: "CUS-005", name: "Charlie Davis", email: "charlie@example.com", tier: "premium", orders: 15, total_spent: 3200.00, country: "USA" },
    { id: "CUS-006", name: "Emma Evans", email: "emma@example.com", tier: "standard", orders: 5, total_spent: 275.00, country: "Canada" },
  ]
};

const supportData = {
  tickets: [
    { id: "TKT-001", subject: "Login issue", customer: "John Smith", priority: "high", status: "open", category: "Authentication", agent: "Agent Smith", created: dates[1], resolved: null, rating: null },
    { id: "TKT-002", subject: "Billing question", customer: "Jane Doe", priority: "medium", status: "closed", category: "Billing", agent: "Agent Johnson", created: dates[3], resolved: dates[4], rating: 5 },
    { id: "TKT-003", subject: "Feature request", customer: "Bob Wilson", priority: "low", status: "open", category: "Product", agent: null, created: dates[5], resolved: null, rating: null },
    { id: "TKT-004", subject: "Bug report", customer: "Alice Brown", priority: "high", status: "in_progress", category: "Technical", agent: "Agent Smith", created: dates[8], resolved: null, rating: null },
    { id: "TKT-005", subject: "Account recovery", customer: "Charlie Davis", priority: "high", status: "closed", category: "Authentication", agent: "Agent Lee", created: dates[10], resolved: dates[10], rating: 4 },
    { id: "TKT-006", subject: "Refund request", customer: "Emma Evans", priority: "medium", status: "closed", category: "Billing", agent: "Agent Johnson", created: dates[12], resolved: dates[14], rating: 3 },
    { id: "TKT-007", subject: "Integration help", customer: "Frank Ford", priority: "low", status: "open", category: "Technical", agent: null, created: dates[15], resolved: null, rating: null },
    { id: "TKT-008", subject: "Password reset", customer: "Grace Green", priority: "high", status: "closed", category: "Authentication", agent: "Agent Smith", created: dates[18], resolved: dates[18], rating: 5 },
    { id: "TKT-009", subject: "Upgrade question", customer: "Henry Hill", priority: "medium", status: "in_progress", category: "Billing", agent: "Agent Johnson", created: dates[20], resolved: null, rating: null },
    { id: "TKT-010", subject: "API documentation", customer: "Ivy Irwin", priority: "low", status: "closed", category: "Product", agent: "Agent Lee", created: dates[22], resolved: dates[25], rating: 4 },
  ],
  agents: [
    { id: "AGT-001", name: "Agent Smith", team: "Tier 1", tickets_handled: 45, avg_rating: 4.2, satisfaction: 92 },
    { id: "AGT-002", name: "Agent Johnson", team: "Tier 1", tickets_handled: 38, avg_rating: 4.5, satisfaction: 95 },
    { id: "AGT-003", name: "Agent Lee", team: "Tier 2", tickets_handled: 22, avg_rating: 4.8, satisfaction: 98 },
  ]
};

const marketingData = {
  campaigns: [
    { id: "CMP-001", name: "Summer Sale", channel: "email", budget: 5000, spent: 4200, leads: 1250, conversions: 85, start_date: dates[1], end_date: dates[30], status: "active" },
    { id: "CMP-002", name: "Product Launch", channel: "social", budget: 8000, spent: 7800, leads: 2100, conversions: 120, start_date: dates[5], end_date: dates[40], status: "active" },
    { id: "CMP-003", name: "Webinar Series", channel: "webinar", budget: 2000, spent: 1800, leads: 450, conversions: 35, start_date: dates[10], end_date: dates[50], status: "completed" },
    { id: "CMP-004", name: "Retargeting Ads", channel: "display", budget: 3000, spent: 2900, leads: 890, conversions: 55, start_date: dates[15], end_date: dates[45], status: "active" },
    { id: "CMP-005", name: "Content Marketing", channel: "organic", budget: 1500, spent: 1200, leads: 380, conversions: 28, start_date: dates[20], end_date: dates[60], status: "active" },
    { id: "CMP-006", name: "Partner Referral", channel: "referral", budget: 1000, spent: 800, leads: 220, conversions: 42, start_date: dates[25], end_date: dates[55], status: "completed" },
  ],
  leads: [
    { id: "L-001", name: "John Smith", company: "Acme Corp", source: "organic", status: "qualified", score: 85, created: dates[1], converted: dates[15] },
    { id: "L-002", name: "Jane Doe", company: "TechStart", source: "email", status: "qualified", score: 72, created: dates[3], converted: null },
    { id: "L-003", name: "Bob Wilson", company: "GlobalTech", source: "referral", status: "qualified", score: 90, created: dates[5], converted: dates[20] },
    { id: "L-004", name: "Alice Brown", company: "StartupXYZ", source: "social", status: "unqualified", score: 35, created: dates[8], converted: null },
    { id: "L-005", name: "Charlie Davis", company: "FinanceFirst", source: "organic", status: "qualified", score: 78, created: dates[10], converted: dates[25] },
    { id: "L-006", name: "Emma Evans", company: "HealthPlus", source: "webinar", status: "qualified", score: 82, created: dates[12], converted: null },
    { id: "L-007", name: "Frank Ford", company: "MediaGroup", source: "display", status: "new", score: 45, created: dates[18], converted: null },
    { id: "L-008", name: "Grace Green", company: "DataSecure", source: "email", status: "qualified", score: 68, created: dates[22], converted: null },
  ]
};

const financeData = {
  transactions: [
    { id: "TXN-001", type: "income", category: "Subscriptions", amount: 15000, client: "Acme Corp", date: dates[1], status: "completed", payment_method: "bank_transfer" },
    { id: "TXN-002", type: "expense", category: "Salaries", amount: 8500, client: null, date: dates[2], status: "completed", payment_method: "bank_transfer" },
    { id: "TXN-003", type: "income", category: "One-time Sale", amount: 5000, client: "TechStart", date: dates[5], status: "completed", payment_method: "credit_card" },
    { id: "TXN-004", type: "expense", category: "Marketing", amount: 2200, client: null, date: dates[8], status: "completed", payment_method: "credit_card" },
    { id: "TXN-005", type: "income", category: "Subscriptions", amount: 15000, client: "GlobalTech", date: dates[10], status: "completed", payment_method: "bank_transfer" },
    { id: "TXN-006", type: "expense", category: "Software", amount: 450, client: null, date: dates[12], status: "completed", payment_method: "credit_card" },
    { id: "TXN-007", type: "income", category: "Consulting", amount: 8000, client: "FinanceFirst", date: dates[15], status: "pending", payment_method: "bank_transfer" },
    { id: "TXN-008", type: "expense", category: "Rent", amount: 3000, client: null, date: dates[18], status: "completed", payment_method: "bank_transfer" },
    { id: "TXN-009", type: "income", category: "Subscriptions", amount: 15000, client: "HealthPlus", date: dates[20], status: "completed", payment_method: "bank_transfer" },
    { id: "TXN-010", type: "expense", category: "Utilities", amount: 380, client: null, date: dates[22], status: "completed", payment_method: "credit_card" },
    { id: "TXN-011", type: "income", category: "One-time Sale", amount: 12000, client: "RetailMax", date: dates[25], status: "completed", payment_method: "bank_transfer" },
    { id: "TXN-012", type: "expense", category: "Salaries", amount: 8500, client: null, date: dates[28], status: "completed", payment_method: "bank_transfer" },
  ],
  invoices: [
    { id: "INV-001", client: "Acme Corp", amount: 15000, status: "paid", issued: dates[1], due: dates[31], paid: dates[15] },
    { id: "INV-002", client: "TechStart", amount: 5000, status: "paid", issued: dates[5], due: dates[35], paid: dates[20] },
    { id: "INV-003", client: "GlobalTech", amount: 15000, status: "paid", issued: dates[10], due: dates[40], paid: dates[25] },
    { id: "INV-004", client: "FinanceFirst", amount: 8000, status: "overdue", issued: dates[15], due: dates[45], paid: null },
    { id: "INV-005", client: "HealthPlus", amount: 15000, status: "paid", issued: dates[20], due: dates[50], paid: dates[35] },
    { id: "INV-006", client: "RetailMax", amount: 12000, status: "pending", issued: dates[25], due: dates[55], paid: null },
  ]
};

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [data, setData] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ chartData: ChartData[]; metadata: Metadata } | null>(null);
  const [error, setError] = useState('');
  const [selectedDataType, setSelectedDataType] = useState('deals');

  const dataCategories = {
    'CRM / Sales': ['deals', 'companies', 'contacts', 'activities', 'owners'],
    'E-commerce': ['orders', 'products', 'customers'],
    'Support': ['tickets', 'agents'],
    'Marketing': ['campaigns', 'leads'],
    'Finance': ['transactions', 'invoices'],
  };

  const sampleDataTypes: Record<string, unknown> = {
    // CRM/Sales
    deals: hubspotLikeData.deals,
    companies: hubspotLikeData.companies,
    contacts: hubspotLikeData.contacts,
    activities: hubspotLikeData.activities,
    owners: hubspotLikeData.owners,
    // E-commerce
    orders: ecommerceData.orders,
    products: ecommerceData.products,
    customers: ecommerceData.customers,
    // Support
    tickets: supportData.tickets,
    agents: supportData.agents,
    // Marketing
    campaigns: marketingData.campaigns,
    leads: marketingData.leads,
    // Finance
    transactions: financeData.transactions,
    invoices: financeData.invoices,
  };

  const sampleDataPrompts: Record<string, string> = {
    // CRM/Sales
    deals: "show me deals by stage with owner breakdown",
    companies: "show me companies by industry with size breakdown",
    contacts: "show me contacts by status with lead status breakdown",
    activities: "show me activities by type with outcome breakdown",
    owners: "show me owners by team with quota achievement",
    // E-commerce
    orders: "show me orders by category with payment breakdown",
    products: "show me products by category with stock levels",
    customers: "show me customers by tier with order count",
    // Support
    tickets: "show me tickets by status with priority breakdown",
    agents: "show me agents by team with tickets handled",
    // Marketing
    campaigns: "show me campaigns by channel with conversion rates",
    leads: "show me leads by source with conversion status",
    // Finance
    transactions: "show me transactions by type with category breakdown",
    invoices: "show me invoices by status with client breakdown",
  };

  const loadSampleData = (dataType: string) => {
    setSelectedDataType(dataType);
    const jsonData: Record<string, unknown> = {};
    jsonData[dataType] = sampleDataTypes[dataType as keyof typeof sampleDataTypes];
    setData(JSON.stringify(jsonData, null, 2));
    setPrompt(sampleDataPrompts[dataType as keyof typeof sampleDataPrompts]);
  };

  const handleGenerate = async () => {
    if (!prompt || !data) {
      setError('Please enter both prompt and data');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const parsedData = JSON.parse(data);
      const response = await fetch('/api/chart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: parsedData, prompt }),
      });

      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(responseData.error || 'Failed to generate chart');
      }

      setResult(responseData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const renderChart = () => {
    if (!result) return null;

    const { chartData, metadata } = result;
    const chartType = metadata.chartType;

    const chartDataFormatted = chartData.map((d: ChartData) => ({
      name: d.x,
      value: d.y,
      series: d.series,
    }));

    const seriesLabels = [...new Set(chartDataFormatted.map((d: any) => d.series).filter(Boolean))];

    if (chartType === 'pie') {
      return (
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie
              data={chartDataFormatted}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={150}
              label
            >
              {chartDataFormatted.map((_: any, index: number) => (
                <Cell key={`cell-${index}`} fill={['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4'][index % 7]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      );
    }

    if (chartType === 'line' || chartType === 'area') {
      const ChartComponent = chartType === 'line' ? LineChart : AreaChart;
      return (
        <ResponsiveContainer width="100%" height={400}>
          <ChartComponent data={chartDataFormatted}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            {seriesLabels.length > 0 ? (
              seriesLabels.map((series: any, i: number) => (
                chartType === 'line' ? (
                  <Line
                    key={series}
                    type="monotone"
                    data={chartDataFormatted.filter((d: any) => d.series === series)}
                    dataKey="value"
                    name={series}
                    stroke={['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'][i % 5]}
                  />
                ) : (
                  <Area
                    key={series}
                    type="monotone"
                    data={chartDataFormatted.filter((d: any) => d.series === series)}
                    dataKey="value"
                    name={series}
                    fill={['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'][i % 5]}
                    stroke={['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'][i % 5]}
                  />
                )
              ))
            ) : (
              chartType === 'line' ? (
                <Line type="monotone" dataKey="value" stroke="#4F46E5" />
              ) : (
                <Area type="monotone" dataKey="value" fill="#4F46E5" stroke="#4F46E5" />
              )
            )}
          </ChartComponent>
        </ResponsiveContainer>
      );
    }

    // Default: Bar chart
    return (
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartDataFormatted}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          {seriesLabels.length > 0 ? (
            seriesLabels.map((series: any, i: number) => (
              <Bar
                key={series}
                dataKey="value"
                name={series}
                fill={['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'][i % 5]}
                stackId="a"
              />
            ))
          ) : (
            <Bar dataKey="value" fill="#4F46E5" />
          )}
        </BarChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Redpill Chart Generator</h1>
        <p className="text-gray-600 mb-8">Generate charts from any JSON data with AI</p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">Choose Sample Data</label>
              {Object.entries(dataCategories).map(([category, types]) => (
                <div key={category} className="mb-3">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{category}</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {types.map((type) => (
                      <button
                        key={type}
                        onClick={() => loadSampleData(type)}
                        className={`px-3 py-1.5 rounded-md text-sm font-medium capitalize ${
                          selectedDataType === type 
                            ? 'bg-blue-600 text-white' 
                            : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Your Prompt</label>
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., show me deals by stage with owner breakdown"
                className="text-black w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">JSON Data</label>
              <textarea
                value={data}
                onChange={(e) => setData(e.target.value)}
                placeholder='{"deals": [...]}'
                rows={10}
                className="text-black w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-xs"
              />
            </div>

            <div className="flex gap-4">
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {loading ? 'Generating...' : 'Generate Chart'}
              </button>
            </div>

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* Chart Section */}
          <div className="bg-white rounded-xl shadow-lg p-6 min-h-[500px]">
            {result ? (
              <div>
                <h2 className="text-lg font-semibold text-gray-800 mb-4">
                  {result.metadata.xAxis?.label || 'Chart'}
                </h2>
                {renderChart()}
                <div className="mt-4 text-sm text-gray-500">
                  <p><span className="font-medium">Chart Type:</span> {result.metadata.chartType}</p>
                  <p><span className="font-medium">X-Axis:</span> {result.metadata.xAxis?.field}</p>
                  <p><span className="font-medium">Y-Axis:</span> {result.metadata.yAxis?.field}</p>
                  {result.metadata.series && <p><span className="font-medium">Series:</span> {result.metadata.series.field}</p>}
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">
                <div className="text-center">
                  <p>Select a sample data type and click Generate Chart</p>
                  <p className="text-sm mt-2">or enter your own JSON data</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
