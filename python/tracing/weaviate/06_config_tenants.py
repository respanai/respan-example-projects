from _protocol import Protocol
from _shared import run_scenario
from weaviate.classes.config import DataType, Property
from weaviate.classes.tenants import Tenant


def scenario():
    with Protocol() as native, native.client() as client:
        col = client.collections.create(
            "Docs", properties=[Property(name="text", data_type=DataType.TEXT)]
        )
        col.config.add_property(Property(name="additional", data_type=DataType.TEXT))
        config = col.config.get()
        col.tenants.create([Tenant(name="tenant")])
        tenants = col.tenants.get()
        listed = client.collections.list_all()
        assert config.name == "Docs" and "tenant" in tenants and "Docs" in listed
        return {
            "collection": config.name,
            "tenant_count": len(tenants),
            "native_config": type(config).__name__,
        }


if __name__ == "__main__":
    run_scenario("config-tenants", scenario)
