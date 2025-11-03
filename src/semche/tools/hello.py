def hello(name: str = "World") -> str:
    """Returns a greeting message.
    
    Args:
        name: Name to greet (optional, defaults to 'World')
        
    Returns:
        Greeting message in the format "Hello, {name}!"
    """
    return f"Hello, {name}!"
