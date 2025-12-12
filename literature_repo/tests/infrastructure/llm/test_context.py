import pytest
from infrastructure.llm.core.context import ConversationContext
from infrastructure.core.exceptions import ContextLimitError

def test_add_message():
    ctx = ConversationContext(max_tokens=100)
    ctx.add_message("user", "Hello")
    assert len(ctx.messages) == 1
    assert ctx.estimated_tokens > 0

def test_prune_context():
    # 1 token ~= 4 chars. 
    # "1234" is 1 token.
    ctx = ConversationContext(max_tokens=2) 
    
    # Add message (1 token)
    ctx.add_message("user", "1234")
    assert len(ctx.messages) == 1
    
    # Add another (1 token) -> Total 2. OK.
    ctx.add_message("assistant", "5678")
    assert len(ctx.messages) == 2
    
    # Add third (1 token) -> Total 3. Should prune first.
    ctx.add_message("user", "9012")
    assert len(ctx.messages) == 2
    assert ctx.messages[0].content == "5678"
    assert ctx.messages[1].content == "9012"

def test_system_prompt_preservation():
    ctx = ConversationContext(max_tokens=3)
    
    ctx.add_message("system", "SYS") # 0 tokens (short)
    ctx.add_message("user", "MSG1") 
    ctx.add_message("asst", "MSG2")
    
    # Add message that forces prune
    # Assuming lengths cause prune.
    # Let's use longer strings
    ctx = ConversationContext(max_tokens=10)
    ctx.add_message("system", "1234") # 1 token
    ctx.add_message("user", "12341234") # 2 tokens
    ctx.add_message("asst", "12341234") # 2 tokens
    
    # Add huge message
    ctx.add_message("user", "1234" * 6) # 6 tokens. Total would be 11.
    
    # Should keep system, remove user msg1
    assert ctx.messages[0].role == "system"
    assert ctx.messages[-1].content == "1234" * 6

def test_context_limit_error():
    ctx = ConversationContext(max_tokens=1)
    with pytest.raises(ContextLimitError):
        ctx.add_message("user", "12341234") # 2 tokens

