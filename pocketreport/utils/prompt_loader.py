"""
Utility function for loading and managing prompts from centralized configuration.
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import tomllib  # Python 3.11+ built-in TOML library


# Cache for prompts to avoid repeated file I/O
_prompt_cache: Optional[Dict[str, Any]] = None


def _get_config_path() -> Path:
    """Get the path to the prompts.toml configuration file."""
    # Look for config directory relative to the project root
    # This file is at pocketreport/utils/prompt_loader.py
    # Config is at /config/prompts.toml (project root)
    current_dir = Path(__file__).parent.parent.parent  # Go up to project root
    config_path = current_dir / "config" / "prompts.toml"
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Prompts configuration file not found at {config_path}. "
            "Please ensure config/prompts.toml exists in the project root."
        )
    
    return config_path


def _load_prompts_from_file() -> Dict[str, Any]:
    """Load prompts from TOML file (internal caching)."""
    global _prompt_cache
    
    if _prompt_cache is not None:
        return _prompt_cache
    
    config_path = _get_config_path()
    
    try:
        with open(config_path, 'rb') as f:
            _prompt_cache = tomllib.load(f)
        logging.debug(f"Loaded prompts from {config_path}")
        return _prompt_cache
    except Exception as e:
        raise RuntimeError(f"Failed to load prompts from {config_path}: {e}")


def get_prompt(
    agent_name: str,
    prompt_type: str = "system_prompt",
    template_vars: Optional[Dict[str, str]] = None
) -> str:
    """
    Get a prompt template from the configuration.
    
    Args:
        agent_name: Name of the agent section (e.g., "analyst", "architect", "writer")
        prompt_type: Type of prompt ("system_prompt" or "user_prompt_template")
        template_vars: Optional dictionary of variables to substitute in user_prompt_template
                      (e.g., {"topic": "AI", "raw_content": "..."})
    
    Returns:
        The prompt string, with template variables substituted if provided
        
    Raises:
        KeyError: If agent or prompt type not found in config
        RuntimeError: If configuration file cannot be loaded
    
    Examples:
        # Get system prompt for analyst
        system_prompt = get_prompt("analyst", "system_prompt")
        
        # Get user prompt with template variable substitution
        user_prompt = get_prompt(
            "architect",
            "user_prompt_template",
            template_vars={"topic": "AI Report", "analysis_summary": "..."}
        )
    """
    prompts = _load_prompts_from_file()
    
    if agent_name not in prompts:
        raise KeyError(f"Agent '{agent_name}' not found in prompts configuration")
    
    agent_section = prompts[agent_name]
    
    if prompt_type not in agent_section:
        raise KeyError(f"Prompt type '{prompt_type}' not found for agent '{agent_name}'")
    
    prompt = agent_section[prompt_type]
    
    # Substitute template variables if provided
    if template_vars and prompt_type == "user_prompt_template":
        try:
            prompt = prompt.format(**template_vars)
        except KeyError as e:
            raise ValueError(
                f"Missing required template variable {e} for agent '{agent_name}'. "
                f"Provided variables: {list(template_vars.keys())}"
            )
    
    return prompt


def get_system_prompt(agent_name: str) -> str:
    """
    Convenience function to get the system prompt for an agent.
    
    Args:
        agent_name: Name of the agent (e.g., "analyst", "architect", "writer")
        
    Returns:
        The system prompt string
    """
    return get_prompt(agent_name, "system_prompt")


def get_user_prompt_template(agent_name: str) -> str:
    """
    Convenience function to get the user prompt template for an agent.
    
    Args:
        agent_name: Name of the agent (e.g., "analyst", "architect", "writer")
        
    Returns:
        The user prompt template string (with placeholders like {topic}, {raw_content})
    """
    return get_prompt(agent_name, "user_prompt_template")


def get_user_prompt(agent_name: str, **template_vars) -> str:
    """
    Convenience function to get the user prompt with template variables substituted.
    
    Args:
        agent_name: Name of the agent (e.g., "analyst", "architect", "writer")
        **template_vars: Keyword arguments for template variable substitution
                        (e.g., topic="AI", raw_content="...")
        
    Returns:
        The user prompt string with variables substituted
        
    Examples:
        prompt = get_user_prompt(
            "architect",
            topic="AI Report",
            analysis_summary="Summary of AI..."
        )
    """
    return get_prompt(agent_name, "user_prompt_template", template_vars=template_vars)


def clear_cache() -> None:
    """Clear the in-memory prompt cache (useful for testing or config reloads)."""
    global _prompt_cache
    _prompt_cache = None
    logging.debug("Prompt cache cleared")


if __name__ == "__main__":
    # Test script to verify prompt loading
    import pprint
    
    logging.basicConfig(level=logging.DEBUG)
    
    # Test loading all prompts
    print("=" * 80)
    print("Testing Prompt Loader")
    print("=" * 80)
    
    try:
        # Test system prompts
        for agent in ["analyst", "architect", "writer"]:
            system_prompt = get_system_prompt(agent)
            print(f"\n[{agent.upper()} - System Prompt]")
            print(f"{system_prompt[:200]}...")
        
        # Test user prompts
        print("\n[ARCHITECT - User Prompt Template]")
        template = get_user_prompt_template("architect")
        print(template)
        
        # Test with variable substitution
        print("\n[ANALYST - User Prompt with Variables]")
        user_prompt = get_user_prompt(
            "analyst",
            raw_content="This is test content"
        )
        print(user_prompt)
        
        print("\n✓ All prompts loaded successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        exit(1)
