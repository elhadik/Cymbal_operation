from google import genai
import inspect
print(inspect.signature(genai.Client().aio.live.connect().__aenter__.__code__))
