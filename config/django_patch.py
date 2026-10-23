"""
Simple Django Context patch for Python 3.14+
"""
import sys
import django.template.context
from django.template.context import Context

# Only apply for Python 3.14+
if sys.version_info >= (3, 14):
    try:
        # Store original __copy__ method
        original_copy = django.template.context.Context.__copy__
        
        def patched_copy(self):
            """Fixed copy without recursion"""
            try:
                # Try the original method first
                return original_copy(self)
            except (AttributeError, TypeError):
                # If original fails, create a new Context manually
                # This avoids recursion by not calling super()
                duplicate = Context(
                    self.dicts[:] if hasattr(self, 'dicts') else [],
                    autoescape=getattr(self, 'autoescape', False),
                    use_l10n=getattr(self, 'use_l10n', False),
                    use_tz=getattr(self, 'use_tz', False)
                )
                # Copy dicts
                if hasattr(self, 'dicts'):
                    duplicate.dicts = self.dicts[:]
                return duplicate
        
        # Apply the patch
        django.template.context.Context.__copy__ = patched_copy
        print("✅ Django Context patched for Python 3.14")
        
    except Exception as e:
        print(f"⚠️ Could not patch Django Context: {e}")