from config import *
from functions_authentication import *
from functions_search import *

def register_route_backend_chats(app):
    @app.route('/api/chat', methods=['POST'])
    @login_required
    def chat_api():
        settings = get_settings()
        data = request.get_json()
        user_id = get_current_user_id()
        if not user_id:
            print("User not authenticated.")
            return jsonify({'error': 'User not authenticated'}), 401

        user_message = data['message']
        conversation_id = data.get('conversation_id')
        hybrid_search_enabled = data.get('hybrid_search', True)  # Default to True if not provided

        # Convert hybrid_search_enabled to boolean if necessary
        if isinstance(hybrid_search_enabled, str):
            hybrid_search_enabled = hybrid_search_enabled.lower() == 'true'

        # Retrieve or create the conversation
        if not conversation_id:
            # Generate a new conversation ID
            conversation_id = str(uuid.uuid4())
            conversation_item = {
                'id': conversation_id,
                'user_id': user_id,
                'messages': [],
                'last_updated': datetime.utcnow().isoformat()
            }
            print(f"Started new conversation {conversation_id}.")
        else:
            # Retrieve existing conversation
            try:
                conversation_item = container.read_item(
                    item=conversation_id,
                    partition_key=conversation_id
                )
                print(f"Retrieved conversation {conversation_id}.")
            except CosmosResourceNotFoundError:
                # Start a new conversation if not found
                conversation_id = str(uuid.uuid4())
                conversation_item = {
                    'id': conversation_id,
                    'user_id': user_id,
                    'messages': [],
                    'last_updated': datetime.utcnow().isoformat()
                }
                print(f"Conversation {conversation_id} not found. Started new conversation.")
            except Exception as e:
                print(f"Error retrieving conversation {conversation_id}: {str(e)}", exc_info=True)
                return jsonify({'error': 'An error occurred'}), 500

        # Append the new user message
        conversation_item['messages'].append({'role': 'user', 'content': user_message})

        # Update the conversation title if it's the first user message
        if conversation_item.get('title') == 'New Conversation':
            new_title = user_message.strip()
            if len(new_title) > 30:
                new_title = new_title[:27] + '...'
            conversation_item['title'] = new_title

        if len(conversation_item['messages']) == 1 and settings.get('default_system_prompt'):
            conversation_item['messages'].insert(0, {'role': 'system', 'content': settings.get('default_system_prompt')})

        # If hybrid search is enabled, perform it and include the results
        if hybrid_search_enabled:
            search_results = hybrid_search(user_message, user_id, top_n=3)
            if search_results:
                # Construct a system prompt with retrieved chunks and citations
                retrieved_texts = []
                for doc in search_results:
                    chunk_text = doc['chunk_text']
                    file_name = doc['file_name']
                    version = doc['version']
                    chunk_sequence = doc['chunk_sequence']
                    page_number = doc.get('page_number') or chunk_sequence  # Use page number if available
                    citation_id = doc['id']  # Use the chunk's unique ID

                    # Create a readable citation string with embedded citation ID
                    citation = f"(Source: {file_name}, Page: {page_number}) [#{citation_id}]"

                    # Append the chunk text with the citation
                    retrieved_texts.append(f"{chunk_text}\n{citation}")
                # Combine all retrieved texts
                retrieved_content = "\n\n".join(retrieved_texts)
                # Create the system prompt with examples
                system_prompt = (
                    "You are an AI assistant provided with the following document excerpts and their sources.\n"
                    "When you answer the user's question, please cite the sources by including the citations provided after each excerpt.\n"
                    "Use the format (Source: filename, Page: page number) [#ID] for citations, where ID is the unique identifier provided.\n"
                    "Ensure your response is informative and includes citations using this format.\n\n"
                    "For example:\n"
                    "User: What is the policy on double dipping?\n"
                    "Assistant: The policy prohibits entities from using federal funds received through one program to apply for additional funds through another program, commonly known as 'double dipping' (Source: PolicyDocument.pdf, Page: 12) [#123abc].\n\n"
                    f"{retrieved_content}"
                )
                # Add system prompt to conversation
                conversation_item['messages'].append({'role': 'system', 'content': system_prompt})
                print("System prompt with hybrid search results added to conversation.")

                container.upsert_item(body=conversation_item)

        # Limit the conversation history
        conversation_history_limit = settings.get('conversation_history_limit', 10)
        conversation_history = conversation_item['messages'][-conversation_history_limit:]

        # Prepare conversation history for API
        allowed_roles = ['system', 'assistant', 'user', 'function', 'tool']
        conversation_history_for_api = []
        for msg in conversation_history:
            if msg['role'] in allowed_roles:
                conversation_history_for_api.append(msg)
            elif msg['role'] == 'file':
                # Modify 'file' messages to be 'system' messages
                file_content = msg.get('file_content', '')
                filename = msg.get('filename', 'uploaded_file')
                # Optionally limit the length of file content to avoid exceeding token limits
                max_file_content_length = 50000  # Adjust as needed based on token limits
                if len(file_content) > max_file_content_length:
                    file_content = file_content[:max_file_content_length] + '...'

                # Create a system message with the file content
                system_message = {
                    'role': 'system',
                    'content': f"The user has uploaded a file named '{filename}' with the following content:\n\n{file_content}\n\nPlease use this information to assist the user."
                }
                conversation_history_for_api.append(system_message)
            else:
                # Ignore messages with other roles
                continue

        # Generate AI response
        response = openai.ChatCompletion.create(
            engine=settings.get('llm_model', 'gpt-4o'),
            messages=conversation_history_for_api
        )

        ai_message = response['choices'][0]['message']['content']
        conversation_item['messages'].append({'role': 'assistant', 'content': ai_message})
        conversation_item['last_updated'] = datetime.utcnow().isoformat()

        # Upsert the conversation item in Cosmos DB
        container.upsert_item(body=conversation_item)
        print("AI response generated and conversation updated.")

        return jsonify({
            'reply': ai_message,
            'conversation_id': conversation_id,
            'conversation_title': conversation_item['title']
        })