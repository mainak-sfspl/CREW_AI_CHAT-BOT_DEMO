from backend.db_tool import ITSupportTools

# Access the function directly from the class (standard CrewAI/LangChain pattern)
tool_instance = ITSupportTools()
print("🔍 Searching for 'asset declaration'...")
result = ITSupportTools.search_documents.run("How often must branches submit the Monthly Asset Declaration?")
print(f"\nRESULTS:\n{result}")
