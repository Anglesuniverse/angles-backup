#!/usr/bin/env python3
"""
Examples for Angles AI Universe™ File Manager
Demonstrates all capabilities and usage patterns

Run this file to see the file manager in action with various scenarios.
"""

from file_manager import FileManager, save_memory_log, save_decision_export, save_strategic_doc, save_agent_log
from datetime import datetime

def example_basic_operations():
    """Demonstrate basic file operations"""
    print("\n🔧 BASIC FILE OPERATIONS")
    print("=" * 50)
    
    fm = FileManager()
    
    # 1. Save files to different folders
    print("1. Saving files to different folders:")
    
    # Memory log
    memory_content = """AI Decision: Use microservices architecture
    Reasoning: Better scalability and maintainability
    Confidence: 0.85
    Date: 2025-08-07"""
    
    result = fm.save_file("memory_logs", memory_content, "architecture-decision.txt")
    print(f"   ✓ Memory log: {result['message']}")
    
    # Decision export  
    decision_content = """STRATEGIC DECISION EXPORT
    
    Decision ID: SD-001
    Type: Technical Architecture
    Status: Approved
    
    Decision: Implement microservices for backend
    Impact: High
    Timeline: Q1 2025
    
    Stakeholders:
    - Backend Team
    - DevOps Team
    - Product Team
    
    Next Actions:
    1. Design service boundaries
    2. Set up service mesh
    3. Implement API gateway
    """
    
    result = fm.save_file("decision_exports", decision_content, "SD-001-microservices.md")
    print(f"   ✓ Decision export: {result['message']}")
    
    # Strategic document
    strategic_content = """# Angles AI Universe™ Technical Strategy 2025
    
    ## Core Principles
    1. AI-First Development
    2. Modular Architecture  
    3. Persistent Memory Systems
    4. Cross-Platform Compatibility
    
    ## Technology Stack
    - Backend: Python + FastAPI
    - Database: PostgreSQL (Supabase)
    - AI Integration: OpenAI, Anthropic
    - Memory: Custom persistence layer
    
    ## Goals
    - [ ] Implement decision tracking
    - [ ] Build memory bridge
    - [ ] Create agent framework
    - [ ] Deploy production system
    """
    
    result = fm.save_file("strategic_docs", strategic_content, "technical-strategy-2025.md")
    print(f"   ✓ Strategic doc: {result['message']}")
    
    return fm

def example_append_operations(fm):
    """Demonstrate append operations"""
    print("\n📝 APPEND OPERATIONS")
    print("=" * 50)
    
    # Append to existing memory log
    additional_content = """
    
    UPDATE: Architecture review completed
    Feedback: Positive from all teams
    Next Step: Start implementation
    Updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    result = fm.append_to_file("memory_logs", "architecture-decision.txt", additional_content)
    print(f"✓ Appended update: {result['message']}")
    
    # Read the updated file to show it worked
    read_result = fm.read_file("memory_logs", "architecture-decision.txt")
    if read_result["success"]:
        print(f"📄 Updated file preview:\n{read_result['content'][-100:]}...")

def example_list_operations(fm):
    """Demonstrate listing operations"""
    print("\n📋 LIST OPERATIONS")
    print("=" * 50)
    
    folders = ["memory_logs", "decision_exports", "strategic_docs", "agents", "tmp"]
    
    for folder in folders:
        result = fm.list_files(folder)
        if result["success"]:
            print(f"\n📁 {folder.upper()}:")
            if result["files"]:
                for file_info in result["files"][:3]:  # Show first 3 files
                    size_kb = file_info["size_bytes"] / 1024
                    print(f"   📄 {file_info['filename']} ({size_kb:.1f} KB)")
            else:
                print("   (no files)")

def example_agent_logs(fm):
    """Demonstrate agent logging"""
    print("\n🤖 AGENT LOGGING")
    print("=" * 50)
    
    # Different agent logs
    agents = {
        "memory_agent": "Started memory sync process. Found 5 unsynced decisions. Processing...",
        "decision_agent": "Analyzing decision impact. High confidence recommendation: APPROVE",
        "strategy_agent": "Strategic alignment check: 95% aligned with company goals",
        "monitoring_agent": "System health: All services operational. Performance: Optimal"
    }
    
    for agent_name, log_content in agents.items():
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_log = f"[{timestamp}] {agent_name.upper()}: {log_content}"
        
        result = fm.save_file("agents", full_log, f"{agent_name}.log", auto_timestamp=True)
        print(f"   ✓ {agent_name}: {result['message']}")

def example_convenience_functions():
    """Demonstrate convenience functions"""
    print("\n🚀 CONVENIENCE FUNCTIONS")
    print("=" * 50)
    
    # Use convenience functions for common operations
    
    # Memory log
    memory_result = save_memory_log("AI system initiated self-learning protocol", "learning-protocol")
    print(f"✓ Memory log: {memory_result['message']}")
    
    # Decision export
    decision_result = save_decision_export("Decision: Deploy to production after testing phase completion")
    print(f"✓ Decision export: {decision_result['message']}")
    
    # Strategic document
    strategic_result = save_strategic_doc("# Q2 Roadmap\n\n- AI Memory Enhancement\n- Agent Framework v2\n- Performance Optimization", "q2-roadmap.md")
    print(f"✓ Strategic doc: {strategic_result['message']}")
    
    # Agent log
    agent_result = save_agent_log("Deployment successful. All systems green.", "deployment_agent")
    print(f"✓ Agent log: {agent_result['message']}")

def example_markdown_to_pdf(fm):
    """Demonstrate markdown to PDF conversion (optional)"""
    print("\n📄 MARKDOWN TO PDF CONVERSION")
    print("=" * 50)
    
    # Create a sample markdown file
    markdown_content = """# Angles AI Universe™ Report
    
    ## Executive Summary
    
    The Angles AI Universe™ system demonstrates exceptional capabilities in:
    
    - **Memory Management**: Persistent decision tracking across sessions
    - **File Organization**: Structured document management system
    - **Agent Integration**: Modular agent framework for specialized tasks
    - **Extensibility**: Easy integration with external services
    
    ## Key Metrics
    
    - Files Processed: 25+
    - Decision Accuracy: 94%
    - System Uptime: 99.8%
    
    ## Recommendations
    
    1. Continue memory bridge development
    2. Expand agent capabilities
    3. Implement real-time monitoring
    
    ---
    
    *Generated by Angles AI Universe™ File Manager*
    """
    
    # Save markdown file
    md_result = fm.save_file("strategic_docs", markdown_content, "system-report.md")
    print(f"✓ Markdown saved: {md_result['message']}")
    
    # Try to convert to PDF
    pdf_result = fm.markdown_to_pdf("strategic_docs", "system-report.md")
    if pdf_result["success"]:
        print(f"✓ PDF created: {pdf_result['message']}")
    else:
        print(f"⚠ PDF conversion: {pdf_result['error']}")
        print("   To enable PDF conversion, install: pip install markdown fpdf2")

def example_folder_overview():
    """Show complete folder structure overview"""
    print("\n📊 FOLDER STRUCTURE OVERVIEW")
    print("=" * 50)
    
    fm = FileManager()
    structure = fm.get_folder_structure()
    
    if structure["success"]:
        print(f"📁 Base path: {structure['base_path']}")
        print(f"📊 Total files: {structure['total_files']}")
        print(f"💾 Total size: {structure['total_size_bytes']} bytes\n")
        
        for folder_name, folder_info in structure['folders'].items():
            status = "✓" if folder_info['exists'] else "✗"
            print(f"   {status} {folder_name}: {folder_info['file_count']} files ({folder_info['size_bytes']} bytes)")

def demo_real_world_scenario():
    """Demonstrate a real-world usage scenario"""
    print("\n🌟 REAL-WORLD SCENARIO: AI DECISION TRACKING")
    print("=" * 60)
    
    fm = FileManager()
    
    # Scenario: AI makes a decision and needs to log it
    decision_data = {
        "decision_id": "DEC-2025-001",
        "timestamp": datetime.now().isoformat(),
        "decision": "Recommend switching from SQLite to PostgreSQL",
        "confidence": 0.92,
        "reasoning": [
            "Better performance for concurrent users",
            "Advanced querying capabilities", 
            "Better integration with cloud services",
            "Supabase integration already available"
        ],
        "impact": "Medium",
        "timeline": "2 weeks",
        "stakeholders": ["Backend Team", "DevOps", "Product Manager"]
    }
    
    # Format for different outputs
    
    # 1. Memory log (structured for processing)
    memory_log = f"""DECISION_LOG:{decision_data['decision_id']}
TIMESTAMP:{decision_data['timestamp']}
DECISION:{decision_data['decision']}
CONFIDENCE:{decision_data['confidence']}
IMPACT:{decision_data['impact']}
REASONING:{'; '.join(decision_data['reasoning'])}
STATUS:PENDING_APPROVAL"""
    
    memory_result = fm.save_file("memory_logs", memory_log, f"{decision_data['decision_id']}-log.txt")
    print(f"1. Memory logged: {memory_result['filename']}")
    
    # 2. Decision export (human readable)
    decision_export = f"""# Decision Export: {decision_data['decision_id']}
    
## Decision
{decision_data['decision']}

## Analysis
- **Confidence**: {decision_data['confidence']*100:.1f}%
- **Impact**: {decision_data['impact']}
- **Timeline**: {decision_data['timeline']}

## Reasoning
{chr(10).join(f'- {reason}' for reason in decision_data['reasoning'])}

## Stakeholders
{chr(10).join(f'- {stakeholder}' for stakeholder in decision_data['stakeholders'])}

## Status
🔄 Pending approval

---
*Generated: {decision_data['timestamp']}*
"""
    
    export_result = fm.save_file("decision_exports", decision_export, f"{decision_data['decision_id']}-export.md")
    print(f"2. Export created: {export_result['filename']}")
    
    # 3. Agent activity log
    agent_activity = f"DECISION_AGENT: Generated recommendation {decision_data['decision_id']} with {decision_data['confidence']*100:.1f}% confidence"
    agent_result = save_agent_log(agent_activity, "decision_agent")
    print(f"3. Agent log: {agent_result['filename']}")
    
    print(f"\n✅ Complete decision tracking workflow executed successfully!")

def main():
    """Run all examples"""
    print("🚀 ANGLES AI UNIVERSE™ FILE MANAGER")
    print("🔧 COMPREHENSIVE EXAMPLES & DEMOS")
    print("=" * 60)
    
    try:
        # Run all examples
        fm = example_basic_operations()
        example_append_operations(fm)
        example_list_operations(fm)
        example_agent_logs(fm)
        example_convenience_functions()
        example_markdown_to_pdf(fm)
        example_folder_overview()
        demo_real_world_scenario()
        
        print("\n" + "=" * 60)
        print("🎉 ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("📁 File Manager is ready for production use")
        print("🔧 Extend as needed for your specific use cases")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()