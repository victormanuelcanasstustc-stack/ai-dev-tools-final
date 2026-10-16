import asyncio
from mcp_server.server import mcp


async def comprobar_servidor():
    herramientas = await mcp.list_tools()
    recursos = await mcp.list_resources()
    prompts = await mcp.list_prompts()

    print("\n=== HERRAMIENTAS ===")
    for herramienta in herramientas:
        print("-", herramienta.name)

    print("\n=== RECURSOS ===")
    for recurso in recursos:
        print("-", recurso.uri)

    print("\n=== PROMPTS ===")
    for prompt in prompts:
        print("-", prompt.name)

    assert len(herramientas) >= 5, "Faltan herramientas MCP"
    assert len(recursos) >= 2, "Faltan recursos MCP"
    assert len(prompts) >= 2, "Faltan prompts MCP"

    print("\nServidor MCP: estructura verificada correctamente")


def test_servidor_mcp_completo():
    asyncio.run(comprobar_servidor())