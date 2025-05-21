import requests
import base64

# === Your eBay OAuth App Credentials ===
client_id = "TravelSa-TravelSa-PRD-3a70f81c3-b1e944ab"
client_secret = "PRD-a70f81c31035-0d5f-4b5a-aa47-3b01"
refresh_token = "v^1.1#i^1#f^0#r^0#p^3#I^3#t^H4sIAAAAAAAA/+VZf2gb1x23bCet56VhS1i6kBVFztiPcNK7k0463SJ38q9a/ilLdpyYbM67d++kF53uLnfvZMtbqW1CYPljhbF2gw4WGFu3sZJClmYMupYQaPdH8MbasnS/YGNjI4OsJGkZDLZ3ku0oDk1iyRDB9I99774/Pp/vj/frwOL2js+fHjz9wQ7fI61nF8Fiq8/Hd4KO7dsOPtbWundbC6gR8J1dPLDYvtz290MOLOqWnMGOZRoO9s8XdcORK4OJgGsbsgkd4sgGLGJHpkjOJkdHZCEIZMs2qYlMPeBP9SUCYV6VBKBpgqBE+CgvsVFjzeakmQhoIA7UOMJIiWMQFiPsveO4OGU4FBo0ERCAIHJA5AR+ko/K4bgM+GA8Ks4E/Iex7RDTYCJBEOiuwJUrunYN1ntDhY6DbcqMBLpTyYHseDLV1z82eShUY6t7NQ5ZCqnr3PnUa6rYfxjqLr63G6ciLWddhLDjBELdVQ93GpWTa2DqgF8JtSZqMRhRJUllsYwJypaEcsC0i5DeG4c3QlROq4jK2KCElu8XURYN5QRGdPVpjJlI9fm9PxMu1IlGsJ0I9Pckj05l+zMBfzadts0SUbHqMRUikhgFIBJlaKkNS1h3oIaxzuzZBEF91V/V6Gq0NzjsNQ2VeLFz/GMm7cEMPN4YIqEmRExo3Bi3kxr1gNXKSeuh5Ge83FaT6dK84aUXF1k8/JXH+ydirTJu18JW1UZUABEQjWmQ15AYw/B2bXi9Xn99dHspSqbTIQ8LVmCZK0K7gKmlQ4Q5xMLrFrFNVDksakJY0jCnRuMaF4lrGqeIapTjWd4AxoqC4tL/YZlQhkRxKV4vlY0vKlwTgSwyLZw2dYLKgY0ilRlotTDmnUQgT6klh0Jzc3PBuXDQtHMhAQA+dGR0JIvyuMhyvyZL7i/MkUrVIsy0HCLTssXQzLMKZM6NXKA7bKtpaNNyFus6G1ir3zuwdW8c/RCSvTphEZhkLpqL46DpUKw2RE3FJYLwLFEfKrNKr29kJwgREAYgJsYAiDZEUjdzxBjFNG8+XJp3UfQmh1RfQ9zYXAppc7GqmV1AfHUWkiSJAzEZgIbIJi0rVSy6FCo6TjVZLkUhBsJSQ/Qs133IjXgXqxIqKnQ+d4IW5xqi5i3BMoGaTL1eNwvYaL7pNNM/kOnPDs5Ojg/3jzXENoM1Gzv5SY9ns9VpciI5nGS/0WE9GlOHrMMFySLOU4NTRyd0YaQnE7JMjI7gQql/ileseGF6Jl04oswfFgEYP3gCTg0sSDmwMOXO5RKJhoKUxcjGTTZ1lY7OhUd7UmMLQ3CBpGxtUCjlsyet/HQ5nM6Hszm3dziFBlNDJyZGGyM/mmu2Tt+65XZyvb29Xm8qkna1MWepB3GWPTVEtD/XdPO1IAJNi0PEx0UApXiM5VPiFTGsaRpmJ/Bww8tvk/GdrByfspBb/yed6ePCMAY0iUdhTuFxPBKBSoPrcrOleauWZcc7vm0NNa/Xt4qep+8wA9AiQW/nEERmMWRCl+a9odkKav+DCIUcdvwLVo/+zHLQxlA1Db1cj/ImdIhRYgdG0y7X43BdeRM6ECHTNWg97lZVN6GhubpGdN27FajHYY36ZmAaUC9Tgpy6XBLDqzZnEyoWLFcIqsSxvH55IE02VsQ2wkGiVm8b6wFrY+YQVi7V6lHapMt1yIZJiUZQ1YbjKg6yifUhKCp7+Hps1RMPh/XCplJXVXggVzVaWMU6KWG73NhxHKvExojOujZpriWjukDOZqGGuQ2rJreguifnF3Lzjd0leRFtxluWdDKbnR7PNHbP0odLzbb3wXwsGhWAwvFKJMZFUEzk4oBHHFIkVQrzAsS4sY185WapfenfzUSaj0ViUkQUIw98k7RhoOZG+65vGqE7vy12t1R+/LLvElj2/aLV5wOHwKf5LrB/e9tUe9tH9zqEsrkeakGH5AxIXRsHC7hsQWK37mpZeWxEXRocubWouBenbz4pteyo+bR59kvg8fWPmx1tfGfNl06w7/abbfzOPTvYpl4UeD4aZumdAV2337bzn2jf/YPey5+cnup86d39b2aV9996PPNF6xrYsS7k821raV/2tRR2F1659szHbuxb+PlxM+iPvPvmO3r7797CK5de/9nAs0+vxN55/rMv3jo30IWUaztbL/d8940/OSfHbqoHv4Mvv7TneXt66FtLA8E/fuS5Wz+Jn/3+la+hrpf97+eOf6Ce6z329qXgE5kLU6GnfnXwGxdvfuZZ/18/9U3/L195buTV1689YY9/wfjR0vnZM498+cCeGz36vl+/B8Ze+/F1cl1Nnfxz4OlHnzn2be7UH15+8urCym+6Xtg5kjzw3j8uLM/869j1fX8b/t5/Vq527r744tcvv31pXprtGlp59Svnb6zc+mf6t5+beXTX/lMXOvaefu3318/vOtdx5Uxi4qcfn5amCkevfrXzv8f8L6Djp64szefe+MuZH1Zz+T+TLE1cdB4AAA=="

# === Encode client credentials ===
basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

# === eBay Token Refresh Request ===
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {basic_auth}",
}

data = {
    "grant_type": "refresh_token",
    "refresh_token": refresh_token,
    "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory"
}

response = requests.post("https://api.ebay.com/identity/v1/oauth2/token", headers=headers, data=data)

# === Print the result ===
print(f"\nStatus Code: {response.status_code}")
try:
    print("Response:")
    print(response.json())
except Exception:
    print("Failed to parse JSON response.")
    print(response.text)
