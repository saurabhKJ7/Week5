"""
Custom Banking Workflows and Compliance Chains
Specialized chains for banking-specific use cases and regulatory compliance
"""

import logging
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from enum import Enum

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from pydantic import BaseModel, Field

from src.config import get_settings
from src.vectorstore import BankingVectorStore
from src.retrieval_chains import BankingRetriever

settings = get_settings()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(str, Enum):
    """Risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceStatus(str, Enum):
    """Compliance status classifications"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"
    INSUFFICIENT_INFO = "insufficient_info"

class LoanProductType(str, Enum):
    """Loan product types"""
    PERSONAL = "personal"
    MORTGAGE = "mortgage"
    AUTO = "auto"
    BUSINESS = "business"
    CREDIT_LINE = "credit_line"

# Pydantic Models for Structured Outputs

class RateInformation(BaseModel):
    """Rate information structure"""
    product_type: str = Field(description="Type of loan product")
    base_rate: Optional[float] = Field(description="Base interest rate")
    apr: Optional[float] = Field(description="Annual Percentage Rate")
    rate_range: Optional[Dict[str, float]] = Field(description="Rate range (min/max)")
    terms_available: List[str] = Field(description="Available loan terms")
    conditions: List[str] = Field(description="Rate conditions and requirements")
    effective_date: Optional[str] = Field(description="Rate effective date")
    source_document: Optional[str] = Field(description="Source document reference")

class ComplianceAnalysis(BaseModel):
    """Compliance analysis structure"""
    regulation_type: str = Field(description="Type of regulation being analyzed")
    compliance_status: ComplianceStatus = Field(description="Overall compliance status")
    requirements: List[str] = Field(description="List of regulatory requirements")
    gaps: List[str] = Field(description="Identified compliance gaps")
    recommendations: List[str] = Field(description="Recommended actions")
    risk_level: RiskLevel = Field(description="Associated risk level")
    deadline: Optional[str] = Field(description="Compliance deadline if applicable")
    regulatory_reference: Optional[str] = Field(description="Regulatory reference/citation")

class LoanEligibility(BaseModel):
    """Loan eligibility analysis"""
    product_type: LoanProductType = Field(description="Loan product type")
    eligible: bool = Field(description="Whether applicant appears eligible")
    requirements_met: List[str] = Field(description="Requirements that are met")
    requirements_missing: List[str] = Field(description="Missing requirements")
    additional_documentation: List[str] = Field(description="Additional documentation needed")
    risk_factors: List[str] = Field(description="Identified risk factors")
    recommendations: List[str] = Field(description="Recommendations for approval")

class PolicyGuidance(BaseModel):
    """Policy guidance structure"""
    policy_area: str = Field(description="Area of policy")
    guidance: str = Field(description="Policy guidance")
    procedures: List[str] = Field(description="Required procedures")
    exceptions: List[str] = Field(description="Policy exceptions")
    escalation_required: bool = Field(description="Whether escalation is required")
    responsible_department: Optional[str] = Field(description="Responsible department")

class RateInquiryWorkflow:
    """
    Workflow for handling rate and pricing inquiries
    """
    
    def __init__(self, vector_store: BankingVectorStore):
        self.vector_store = vector_store
        self.retriever = BankingRetriever(vector_store, search_type="tables")
        
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,
            api_key=settings.openai_api_key
        )
        
        # Create rate inquiry prompt
        self.rate_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a banking rate specialist. Analyze the provided rate sheets and pricing documents to extract accurate rate information.

CRITICAL REQUIREMENTS:
1. Only provide rates that are explicitly stated in the documents
2. Always include the effective date if available
3. Distinguish between base rates and APR
4. Include all relevant terms and conditions
5. Note any rate ranges or tiers
6. Specify the source document for verification

RESPONSE FORMAT:
Provide a structured response with:
- Product type
- Base rate and APR (if different)
- Rate ranges or tiers
- Available terms
- Conditions and requirements
- Effective date
- Source reference

If rate information is not found or unclear, state this explicitly."""),
            ("human", "Rate inquiry for: {product_type}\n\nContext from rate sheets:\n{context}\n\nPlease provide accurate rate information.")
        ])
        
        self.rate_chain = self.rate_prompt | self.llm | PydanticOutputParser(pydantic_object=RateInformation)
    
    def get_rates(self, product_type: str, specific_terms: Optional[str] = None) -> RateInformation:
        """Get current rates for a specific product type"""
        
        try:
            # Enhanced query for rate information
            query = f"current interest rates for {product_type}"
            if specific_terms:
                query += f" {specific_terms}"
            
            # Retrieve rate documents
            rate_docs = self.retriever.get_relevant_documents(query)
            
            if not rate_docs:
                return RateInformation(
                    product_type=product_type,
                    conditions=["No current rate information available"],
                    terms_available=[]
                )
            
            # Combine rate document context
            context = "\n\n".join([
                f"Document: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
                for doc in rate_docs
            ])
            
            # Generate structured response
            result = self.rate_chain.invoke({
                "product_type": product_type,
                "context": context
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Rate inquiry error: {e}")
            return RateInformation(
                product_type=product_type,
                conditions=[f"Error retrieving rate information: {str(e)}"],
                terms_available=[]
            )

class ComplianceWorkflow:
    """
    Workflow for compliance analysis and regulatory guidance
    """
    
    def __init__(self, vector_store: BankingVectorStore):
        self.vector_store = vector_store
        self.retriever = BankingRetriever(vector_store)
        
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,
            api_key=settings.openai_api_key
        )
        
        # Compliance analysis prompt
        self.compliance_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a banking compliance specialist with expertise in regulatory requirements, policies, and risk management.

ANALYSIS REQUIREMENTS:
1. Identify specific regulatory requirements from the documents
2. Assess compliance status based on available information
3. Highlight any compliance gaps or areas of concern
4. Provide actionable recommendations
5. Assess risk level (low, medium, high, critical)
6. Include relevant regulatory references

COMPLIANCE AREAS TO CONSIDER:
- Consumer protection regulations
- Anti-money laundering (AML)
- Know Your Customer (KYC)
- Fair lending practices
- Data privacy and security
- Capital adequacy
- Operational risk

RISK ASSESSMENT CRITERIA:
- HIGH/CRITICAL: Potential regulatory violations, fines, or legal action
- MEDIUM: Areas requiring attention but not immediately critical
- LOW: Minor issues or best practice improvements

Provide specific, actionable guidance based on the regulatory documents."""),
            ("human", "Compliance analysis request: {regulation_area}\n\nSpecific question or concern: {question}\n\nRelevant regulatory context:\n{context}")
        ])
        
        self.compliance_chain = self.compliance_prompt | self.llm | PydanticOutputParser(pydantic_object=ComplianceAnalysis)
    
    def analyze_compliance(self, regulation_area: str, specific_question: str) -> ComplianceAnalysis:
        """Analyze compliance requirements for a specific area"""
        
        try:
            # Search for compliance documents
            query = f"compliance requirements {regulation_area} {specific_question}"
            compliance_docs = self.vector_store.search_compliance(query, k=10)
            
            if not compliance_docs:
                return ComplianceAnalysis(
                    regulation_type=regulation_area,
                    compliance_status=ComplianceStatus.INSUFFICIENT_INFO,
                    requirements=[],
                    gaps=["Insufficient regulatory documentation available"],
                    recommendations=["Consult with compliance team and review current regulatory guidance"],
                    risk_level=RiskLevel.MEDIUM
                )
            
            # Prepare context from compliance documents
            context = "\n\n".join([
                f"Document: {doc.metadata.get('source', 'Unknown')}\n"
                f"Risk Level: {doc.metadata.get('risk_level', 'Unknown')}\n"
                f"Content: {doc.page_content}"
                for doc in compliance_docs
            ])
            
            # Perform compliance analysis
            result = self.compliance_chain.invoke({
                "regulation_area": regulation_area,
                "question": specific_question,
                "context": context
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Compliance analysis error: {e}")
            return ComplianceAnalysis(
                regulation_type=regulation_area,
                compliance_status=ComplianceStatus.INSUFFICIENT_INFO,
                requirements=[],
                gaps=[f"Analysis error: {str(e)}"],
                recommendations=["Contact compliance team for manual review"],
                risk_level=RiskLevel.HIGH
            )

class LoanUnderwritingWorkflow:
    """
    Workflow for loan underwriting guidance and eligibility analysis
    """
    
    def __init__(self, vector_store: BankingVectorStore):
        self.vector_store = vector_store
        self.retriever = BankingRetriever(vector_store)
        
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,
            api_key=settings.openai_api_key
        )
        
        # Underwriting prompt
        self.underwriting_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior loan underwriter with expertise in loan products, eligibility requirements, and risk assessment.

UNDERWRITING ANALYSIS:
1. Review loan product requirements from policy documents
2. Assess applicant information against eligibility criteria
3. Identify any missing documentation or requirements
4. Evaluate risk factors and mitigation strategies
5. Provide clear recommendations for loan approval/denial

KEY EVALUATION AREAS:
- Credit requirements
- Income verification
- Debt-to-income ratios
- Collateral requirements (if applicable)
- Employment stability
- Regulatory compliance requirements

RISK FACTORS TO CONSIDER:
- Credit history issues
- Income stability concerns
- High debt ratios
- Insufficient documentation
- Regulatory red flags

Provide specific, actionable guidance based on underwriting policies."""),
            ("human", "Loan underwriting analysis for {loan_type}\n\nApplicant profile: {applicant_info}\n\nUnderwriting guidelines:\n{context}")
        ])
        
        self.underwriting_chain = self.underwriting_prompt | self.llm | PydanticOutputParser(pydantic_object=LoanEligibility)
    
    def evaluate_loan_eligibility(
        self, 
        loan_type: str, 
        applicant_info: Dict[str, Any]
    ) -> LoanEligibility:
        """Evaluate loan eligibility based on underwriting guidelines"""
        
        try:
            # Search for underwriting guidelines
            query = f"loan underwriting requirements {loan_type} eligibility criteria"
            underwriting_docs = self.retriever.get_relevant_documents(query)
            
            # Prepare context
            context = "\n\n".join([
                f"Document: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
                for doc in underwriting_docs
            ])
            
            # Format applicant information
            applicant_summary = json.dumps(applicant_info, indent=2)
            
            # Perform underwriting analysis
            result = self.underwriting_chain.invoke({
                "loan_type": loan_type,
                "applicant_info": applicant_summary,
                "context": context
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Underwriting analysis error: {e}")
            return LoanEligibility(
                product_type=LoanProductType.PERSONAL,  # Default
                eligible=False,
                requirements_met=[],
                requirements_missing=[f"Analysis error: {str(e)}"],
                additional_documentation=["Manual underwriting review required"],
                risk_factors=["Unable to complete automated analysis"],
                recommendations=["Refer to senior underwriter for manual review"]
            )

class PolicyGuidanceWorkflow:
    """
    Workflow for policy interpretation and procedural guidance
    """
    
    def __init__(self, vector_store: BankingVectorStore):
        self.vector_store = vector_store
        self.retriever = BankingRetriever(vector_store)
        
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,
            api_key=settings.openai_api_key
        )
        
        # Policy guidance prompt
        self.policy_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a banking policy specialist responsible for interpreting internal policies and procedures.

POLICY GUIDANCE REQUIREMENTS:
1. Locate relevant policy documents and procedures
2. Provide clear interpretation of policy requirements
3. Identify specific procedures that must be followed
4. Highlight any exceptions or escalation requirements
5. Specify responsible departments or roles
6. Include relevant policy references

AREAS OF EXPERTISE:
- Customer service policies
- Operational procedures
- Risk management policies
- Compliance procedures
- Product policies
- Staff guidelines

Provide practical, actionable guidance that staff can immediately implement."""),
            ("human", "Policy guidance request for: {policy_area}\n\nSpecific situation: {situation}\n\nRelevant policy documents:\n{context}")
        ])
        
        self.policy_chain = self.policy_prompt | self.llm | PydanticOutputParser(pydantic_object=PolicyGuidance)
    
    def get_policy_guidance(self, policy_area: str, situation: str) -> PolicyGuidance:
        """Get policy guidance for a specific situation"""
        
        try:
            # Search for policy documents
            query = f"policy procedures {policy_area} {situation}"
            policy_docs = self.retriever.get_relevant_documents(query)
            
            # Filter for policy documents
            policy_docs = [
                doc for doc in policy_docs 
                if doc.metadata.get("document_type") in ["policy_document", "procedure_manual"]
            ]
            
            if not policy_docs:
                return PolicyGuidance(
                    policy_area=policy_area,
                    guidance="No specific policy guidance found for this situation.",
                    procedures=["Consult with supervisor or policy team"],
                    exceptions=[],
                    escalation_required=True,
                    responsible_department="Policy Team"
                )
            
            # Prepare context
            context = "\n\n".join([
                f"Policy Document: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
                for doc in policy_docs
            ])
            
            # Generate policy guidance
            result = self.policy_chain.invoke({
                "policy_area": policy_area,
                "situation": situation,
                "context": context
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Policy guidance error: {e}")
            return PolicyGuidance(
                policy_area=policy_area,
                guidance=f"Error retrieving policy guidance: {str(e)}",
                procedures=["Contact policy team for assistance"],
                exceptions=[],
                escalation_required=True
            )

class BankingWorkflowOrchestrator:
    """
    Orchestrates different banking workflows based on request type
    """
    
    def __init__(self, vector_store: BankingVectorStore):
        self.vector_store = vector_store
        
        # Initialize specialized workflows
        self.rate_workflow = RateInquiryWorkflow(vector_store)
        self.compliance_workflow = ComplianceWorkflow(vector_store)
        self.underwriting_workflow = LoanUnderwritingWorkflow(vector_store)
        self.policy_workflow = PolicyGuidanceWorkflow(vector_store)
        
        # Track workflow usage
        self.usage_stats = {
            "rate_inquiries": 0,
            "compliance_analyses": 0,
            "underwriting_evaluations": 0,
            "policy_requests": 0,
            "total_requests": 0
        }
    
    def route_request(self, request_type: str, **kwargs) -> Dict[str, Any]:
        """Route request to appropriate workflow"""
        
        self.usage_stats["total_requests"] += 1
        
        try:
            if request_type == "rate_inquiry":
                self.usage_stats["rate_inquiries"] += 1
                result = self.rate_workflow.get_rates(
                    product_type=kwargs.get("product_type", ""),
                    specific_terms=kwargs.get("specific_terms")
                )
                
            elif request_type == "compliance_analysis":
                self.usage_stats["compliance_analyses"] += 1
                result = self.compliance_workflow.analyze_compliance(
                    regulation_area=kwargs.get("regulation_area", ""),
                    specific_question=kwargs.get("question", "")
                )
                
            elif request_type == "underwriting_evaluation":
                self.usage_stats["underwriting_evaluations"] += 1
                result = self.underwriting_workflow.evaluate_loan_eligibility(
                    loan_type=kwargs.get("loan_type", ""),
                    applicant_info=kwargs.get("applicant_info", {})
                )
                
            elif request_type == "policy_guidance":
                self.usage_stats["policy_requests"] += 1
                result = self.policy_workflow.get_policy_guidance(
                    policy_area=kwargs.get("policy_area", ""),
                    situation=kwargs.get("situation", "")
                )
                
            else:
                raise ValueError(f"Unknown request type: {request_type}")
            
            # Convert Pydantic model to dict and add metadata
            response = {
                "workflow_type": request_type,
                "timestamp": datetime.now().isoformat(),
                "result": result.dict() if hasattr(result, 'dict') else result,
                "success": True
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Workflow routing error: {e}")
            return {
                "workflow_type": request_type,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get workflow usage statistics"""
        return self.usage_stats.copy()

# Factory functions for easy workflow creation
def create_banking_workflow_orchestrator(vector_store: BankingVectorStore) -> BankingWorkflowOrchestrator:
    """Create a banking workflow orchestrator"""
    return BankingWorkflowOrchestrator(vector_store)

def create_rate_workflow(vector_store: BankingVectorStore) -> RateInquiryWorkflow:
    """Create a rate inquiry workflow"""
    return RateInquiryWorkflow(vector_store)

def create_compliance_workflow(vector_store: BankingVectorStore) -> ComplianceWorkflow:
    """Create a compliance workflow"""
    return ComplianceWorkflow(vector_store)

# Example usage
if __name__ == "__main__":
    from pathlib import Path
    from src.vectorstore import get_banking_vector_store
    
    def test_banking_workflows():
        """Test banking workflows"""
        
        # Initialize vector store
        vector_store = get_banking_vector_store()
        
        # Create workflow orchestrator
        orchestrator = create_banking_workflow_orchestrator(vector_store)
        
        # Test rate inquiry
        print("Testing Rate Inquiry Workflow:")
        rate_result = orchestrator.route_request(
            "rate_inquiry",
            product_type="personal loan",
            specific_terms="fixed rate 36 months"
        )
        print(f"Rate inquiry result: {rate_result}")
        
        # Test compliance analysis
        print("\nTesting Compliance Analysis Workflow:")
        compliance_result = orchestrator.route_request(
            "compliance_analysis",
            regulation_area="fair lending",
            question="What are the documentation requirements for loan applications?"
        )
        print(f"Compliance result: {compliance_result}")
        
        # Test policy guidance
        print("\nTesting Policy Guidance Workflow:")
        policy_result = orchestrator.route_request(
            "policy_guidance",
            policy_area="customer service",
            situation="handling customer complaints about loan denials"
        )
        print(f"Policy guidance result: {policy_result}")
        
        # Get usage statistics
        stats = orchestrator.get_usage_stats()
        print(f"\nWorkflow usage stats: {stats}")
    
    test_banking_workflows() 