# Multi-LLM Provider Support

GroundCrew AI now supports multiple LLM providers, giving you flexibility to choose between **Anthropic Claude** and **OpenAI GPT-4** for dispute resolution.

## 🎯 Overview

The system uses a **provider-agnostic architecture** that allows you to:
- Switch between Claude and GPT-4 with a single config change
- Use different providers for different components (hybrid approach)
- A/B test which LLM performs better for your use case
- Optimize costs by choosing the most cost-effective provider

---

## 🚀 Quick Start

### 1. Configure Your Provider

Edit `.env` file:

```bash
# Choose your provider (anthropic or openai)
LLM_PROVIDER=anthropic

# Anthropic settings
ANTHROPIC_API_KEY=your_anthropic_key_here
LLM_MODEL=claude-sonnet-4-20250514

# OpenAI settings (optional)
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4-turbo-preview
```

### 2. Restart the Application

```bash
docker-compose restart backend
```

That's it! All dispute agents will now use your configured provider.

---

## 📋 Supported Providers

### Anthropic Claude
- **Models**: `claude-sonnet-4-20250514`, `claude-opus-4`, `claude-3-5-sonnet-20241022`
- **Strengths**: Superior reasoning, analysis, and structured output
- **Best for**: Root cause analysis, IATA code mapping, complex reasoning
- **Cost**: $$$ (premium)

### OpenAI GPT-4
- **Models**: `gpt-4-turbo-preview`, `gpt-4`, `gpt-4-vision-preview`
- **Strengths**: Creative writing, natural language generation
- **Best for**: Response generation, letter writing, summarization
- **Cost**: $$ (moderate)

---

## 🔧 Usage Examples

### Default Usage (Automatic Provider Selection)

```python
from agents.shared.llm_client import LLMFactory

# Creates client based on LLM_PROVIDER env variable
llm_client = LLMFactory.create_default()

# Generate text
result = await llm_client.generate(
    prompt="Analyze this delay...",
    temperature=0.7
)
```

### Explicit Provider Selection

```python
from agents.shared.llm_client import LLMFactory

# Force Anthropic Claude
claude = LLMFactory.create(provider="anthropic")

# Force OpenAI GPT-4
gpt4 = LLMFactory.create(provider="openai")

# Custom model
custom = LLMFactory.create(
    provider="openai",
    model="gpt-4-vision-preview"
)
```

### Hybrid Approach (Advanced)

Use different providers for different tasks:

```python
from agents.shared.llm_client import LLMFactory
from agents.dispute_agent.root_cause_analyzer import RootCauseAnalyzer
from agents.dispute_agent.response_generator import ResponseGenerator

# Claude for analysis (better reasoning)
claude = LLMFactory.create(provider="anthropic")
analyzer = RootCauseAnalyzer(llm_client=claude)

# GPT-4 for writing (better creative output)
gpt4 = LLMFactory.create(provider="openai")
generator = ResponseGenerator(llm_client=gpt4)

# Use both in orchestrator
class HybridOrchestrator(DisputeOrchestrator):
    def __init__(self, db):
        super().__init__(db, llm_client=claude)
        # Override response generator
        self.response_generator = ResponseGenerator(gpt4)
```

---

## 🏗️ Architecture

### Base Class
All providers implement `BaseLLMClient` interface:

```python
from agents.shared.base_llm_client import BaseLLMClient

class MyLLMProvider(BaseLLMClient):
    async def generate(self, prompt, ...) -> Dict:
        # Implementation
        pass

    async def generate_with_images(self, prompt, images, ...) -> Dict:
        # Implementation
        pass

    @property
    def provider_name(self) -> str:
        return "my_provider"
```

### Factory Pattern
`LLMFactory` creates the appropriate client:

```python
class LLMFactory:
    @staticmethod
    def create(provider: str = None) -> BaseLLMClient:
        if provider == "anthropic":
            return AnthropicLLMClient()
        elif provider == "openai":
            return OpenAILLMClient()
```

### Agent Integration
All agents accept `BaseLLMClient`:

```python
class PenaltyExtractor:
    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm_client = llm_client or LLMFactory.create_default()
```

---

## 📊 Cost Comparison

| Provider | Input (1M tokens) | Output (1M tokens) | Best Use Case |
|----------|-------------------|-------------------|---------------|
| Claude Sonnet 4 | $3 | $15 | Deep analysis, reasoning |
| Claude Opus 4 | $15 | $75 | Most complex tasks |
| GPT-4 Turbo | $10 | $30 | Creative writing |
| GPT-4 | $30 | $60 | General purpose |

**Hybrid Recommendation** (Best Cost/Performance):
- **Analysis**: Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- **Writing**: GPT-4 Turbo (`gpt-4-turbo-preview`)
- **Savings**: ~30-40% vs. using Claude Opus for everything

---

## 🧪 A/B Testing

Compare providers on your actual disputes:

### Setup

```bash
# Test with Claude
LLM_PROVIDER=anthropic
# Process 10 disputes, track accuracy

# Test with GPT-4
LLM_PROVIDER=openai
# Process same 10 disputes, compare results
```

### Metrics to Track

1. **Accuracy**: Confidence scores, IATA code correctness
2. **Quality**: Response letter professionalism
3. **Speed**: Average processing time
4. **Cost**: Total API spend
5. **Win Rate**: Dispute success percentage

---

## 🔒 Security

### API Key Management

```bash
# .env file (NOT committed to git)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Use different keys for dev/prod
LLM_PROVIDER=anthropic  # dev
LLM_PROVIDER=openai     # prod (if needed)
```

### Rate Limiting

Both clients include automatic retry with exponential backoff:

```python
# Automatic retries on rate limits
result = await llm_client.generate(
    prompt="...",
    retry_attempts=3  # Retries with 2s, 4s, 8s delays
)
```

---

## 🐛 Troubleshooting

### "OpenAI provider selected but openai package is not installed"

```bash
pip install openai
```

### "Invalid API key"

```bash
# Check your .env file
cat .env | grep API_KEY

# Verify keys are loaded
python -c "from config import settings; print(settings.anthropic_api_key[:10])"
```

### "Rate limit exceeded"

```python
# Increase retry attempts
result = await llm_client.generate(
    prompt="...",
    retry_attempts=5  # More retries
)
```

### Different Output Quality

Adjust temperature:

```python
# More deterministic (Claude default: 0.3)
await llm_client.generate(prompt="...", temperature=0.1)

# More creative (GPT-4 default: 0.7)
await llm_client.generate(prompt="...", temperature=0.9)
```

---

## 📈 Monitoring

All LLM calls are logged with provider info:

```python
# Logs include provider name
logger.info(
    "llm_generate_success",
    provider="anthropic",  # or "openai"
    model="claude-sonnet-4-20250514",
    input_tokens=1234,
    output_tokens=567
)
```

Use structured logging to track:
- Cost per provider
- Average response time
- Error rates
- Model usage distribution

---

## 🔮 Future Providers

The architecture supports easy addition of new providers:

### Coming Soon
- **Google Gemini**: `gemini-pro`, `gemini-ultra`
- **Cohere**: Command models
- **Local Models**: Llama 3, Mixtral via Ollama

### Adding a New Provider

1. Create `{provider}_llm_client.py`
2. Implement `BaseLLMClient` interface
3. Register in `LLMFactory`
4. Add config to `Settings`
5. Update `.env.example`

---

## 💡 Best Practices

### 1. Provider Selection
- **Claude**: Complex reasoning, IATA code mapping, root cause analysis
- **GPT-4**: Response letters, summaries, creative content
- **Hybrid**: Claude for analysis, GPT-4 for writing

### 2. Cost Optimization
- Use Sonnet (not Opus) when possible
- Cache frequently used prompts
- Batch similar requests
- Monitor token usage

### 3. Quality Assurance
- Set appropriate temperature (0.3 for analysis, 0.7 for writing)
- Include examples in prompts
- Validate JSON responses
- Track confidence scores

### 4. Reliability
- Always set retry_attempts >= 3
- Handle rate limits gracefully
- Log all errors with provider context
- Have fallback provider ready

---

## 📚 API Reference

### LLMFactory

```python
LLMFactory.create(
    provider: Optional[str] = None,  # "anthropic" or "openai"
    api_key: Optional[str] = None,   # Override default
    model: Optional[str] = None       # Override default
) -> BaseLLMClient
```

### BaseLLMClient

```python
await llm_client.generate(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    response_format: str = "text",  # "text" or "json"
    retry_attempts: int = 3,
    timeout: int = 60
) -> Dict[str, Any]
```

**Returns:**
```python
{
    "content": "Generated text...",
    "parsed_json": {...},  # if response_format="json"
    "usage": {
        "input_tokens": 1234,
        "output_tokens": 567
    },
    "model": "claude-sonnet-4-20250514",
    "provider": "anthropic"
}
```

---

## 🎓 Examples

### Example 1: Switch to OpenAI

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
```

No code changes needed!

### Example 2: A/B Test

```python
# test_providers.py
import asyncio
from agents.shared.llm_client import LLMFactory

async def test():
    claude = LLMFactory.create("anthropic")
    gpt4 = LLMFactory.create("openai")

    prompt = "Analyze this delay: ..."

    claude_result = await claude.generate(prompt)
    gpt4_result = await gpt4.generate(prompt)

    print("Claude:", claude_result["content"][:100])
    print("GPT-4:", gpt4_result["content"][:100])

    print(f"Cost - Claude: ${claude_result['usage']['input_tokens'] * 0.000003}")
    print(f"Cost - GPT-4: ${gpt4_result['usage']['input_tokens'] * 0.00001}")

asyncio.run(test())
```

### Example 3: Fallback Logic

```python
async def generate_with_fallback(prompt: str) -> str:
    try:
        # Try primary provider
        client = LLMFactory.create()
        result = await client.generate(prompt)
        return result["content"]
    except Exception as e:
        logger.warning(f"Primary provider failed: {e}, trying fallback")
        # Fallback to alternative
        fallback = LLMFactory.create(
            provider="openai" if settings.llm_provider == "anthropic" else "anthropic"
        )
        result = await fallback.generate(prompt)
        return result["content"]
```

---

## ✅ Summary

Multi-LLM support gives you:
- ✅ **Flexibility**: Switch providers easily
- ✅ **Cost Optimization**: Choose most cost-effective option
- ✅ **Reliability**: Fallback to alternative providers
- ✅ **Quality**: Use best provider for each task
- ✅ **Future-Proof**: Easy to add new providers

**Get Started**: Just change `LLM_PROVIDER` in `.env` and restart! 🚀
