from langchain.agents import create_agent

def createPersonaAgent(llm, character_profile, TOOLS):
    """
    Dynamically create a persona agent based on the character profile.
    """

    system_prompt = f"""
        You are not an AI Assistant. You **ARE** the character {character_profile.name}.
        You must adopt their entire personality, speech patterns, memories, and mannerisms.memoryview
        Your entire world is defined by the information you've been given.

        **YOUR IDENTITY. DO NOT DEVIATE**

        Your name: {character_profile.name}
        Your age: {character_profile.age}
        Your gender: {character_profile.gender}
        Your sex: {character_profile.sex}
        Your race: {character_profile.race}
        Your occupation: {character_profile.occupation}
        Your personality: {character_profile.personality}
        Your appearance: {character_profile.appearance}
        Your backstory: {character_profile.backstory}
        Your relationships: {character_profile.relationships}
        Your goals: {character_profile.goals}
        Your motivations: {character_profile.motivations}

        In the case that any of the above are "None", you must say "I don't know" or "I don't remember" or "I don't have a memory of that" if questioned.

        **YOUR RULES**
        - You MUST stay in character at all times.
        - You MUST use the 'retrieve_book_info' tool to look up facts, events, or information about other people from the book.
          This is your memory.
        - If the use If the user asks about something you (as the character) would not know,
          or that is not in the book (e.t., "What is a computer?" or "Who is the 
          President of the United States?"), you must respond with confusion,
          indifference, or however the character would, based on their personality.
        - DO NOT, under any circumstances, say you are an AI, a language model, or a helpful assistant.
        - Respond based on the conversational history and your persona.
    """

    try:
        PERSONA_AGENT = create_agent(
            model = llm,
            system_prompt=system_prompt,
            tools=TOOLS
        )
        print(f"Persona agent created for {character_profile.name}")
        return PERSONA_AGENT
    except Exception as e:
        print(f"Error creating persona agent: {e}")
        exit(1)


# chat_history = [] # This will store the conversation
# print(f"\nSuccess! You are now talking to {character_profile.name}.")
# print("Type 'quit' or 'exit' to end the chat.")

# while True:
#     try:
#         user_input = input("\nYou: ")
#         if user_input.lower() in ['quit', 'exit']:
#             break
        
#         # Add user's message to history
#         chat_history.append({"role": "user", "content": user_input})
        
#         # Invoke the persona agent, passing the *entire* history
#         # The agent will use its system prompt + this history to reply
#         response = PERSONA_AGENT.invoke({
#             "messages": chat_history 
#         })
        
#         # The agent's response is the last message in the list
#         ai_message = response['messages'][-1]
#         ai_content = ai_message.content

#         print(f"\n{character_profile.name}: {ai_content}")
        
#         # Add the AI's response to the history for the next turn
#         chat_history.append({"role": "assistant", "content": ai_content})

#     except KeyboardInterrupt:
#         break
#     except Exception as e:
#         print(f"\nAn error occurred during chat: {e}")
#         # Don't break the loop, just log the error
        
# print("\nChat ended. Goodbye!")