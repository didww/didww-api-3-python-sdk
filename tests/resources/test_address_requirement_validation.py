import pytest
from tests.conftest import my_vcr
from didww.resources.address_requirement_validation import AddressRequirementValidation
from didww.resources.address import Address
from didww.resources.requirement import Requirement
from didww.resources.identity import Identity
from didww.exceptions import DidwwApiError


class TestAddressRequirementValidation:
    @my_vcr.use_cassette("address_requirement_validations/create.yaml")
    def test_create_address_requirement_validation_success(self, client):
        rv = AddressRequirementValidation()
        rv.address = Address.build("d3414687-40f4-4346-a267-c2c65117d28c")
        rv.requirement = Requirement.build("aea92b24-a044-4864-9740-89d3e15b65c7")
        response = client.address_requirement_validations().create(rv)
        created = response.data
        assert created.id == "aea92b24-a044-4864-9740-89d3e15b65c7"

    @my_vcr.use_cassette("address_requirement_validations/create_error.yaml")
    def test_create_address_requirement_validation_failure(self, client):
        rv = AddressRequirementValidation()
        rv.identity = Identity.build("5e9df058-50d2-4e34-b0d4-d1746b86f41a")
        rv.address = Address.build("d3414687-40f4-4346-a267-c2c65117d28c")
        rv.requirement = Requirement.build("2efc3427-8ba6-4d50-875d-f2de4a068de8")
        with pytest.raises(DidwwApiError) as exc_info:
            client.address_requirement_validations().create(rv)
        assert exc_info.value.status_code == 422
        assert len(exc_info.value.errors) == 3

    @my_vcr.use_cassette("address_requirement_validations/create_failed.yaml")
    def test_create_address_requirement_validation_with_identity(self, client):
        rv = AddressRequirementValidation()
        rv.identity = Identity.build("5e9df058-50d2-4e34-b0d4-d1746b86f41a")
        rv.address = Address.build("d3414687-40f4-4346-a267-c2c65117d28c")
        rv.requirement = Requirement.build("2efc3427-8ba6-4d50-875d-f2de4a068de8")
        response = client.address_requirement_validations().create(rv)
        created = response.data
        assert created.id == "aea92b24-a044-4864-9740-89d3e15b65c7"

    @my_vcr.use_cassette("address_requirement_validations/create_request_failed.yaml")
    def test_create_address_requirement_validation_echo_response(self, client):
        rv = AddressRequirementValidation()
        rv.identity = Identity.build("5e9df058-50d2-4e34-b0d4-d1746b86f41a")
        rv.address = Address.build("d3414687-40f4-4346-a267-c2c65117d28c")
        rv.requirement = Requirement.build("2efc3427-8ba6-4d50-875d-f2de4a068de8")
        response = client.address_requirement_validations().create(rv)
        created = response.data
        assert created.id is None
