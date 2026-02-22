from didww.enums import IdentityType
from didww.resources.base import DidwwApiModel, SafeAttributeField, EnumAttributeField, RelationField, Repository


class Identity(DidwwApiModel):
    _writable_attrs = {
        "first_name", "last_name", "phone_number", "id_number", "birth_date",
        "company_name", "company_reg_number", "vat_id", "description",
        "personal_tax_id", "identity_type", "external_reference_id", "contact_email",
    }

    first_name = SafeAttributeField("first_name")
    last_name = SafeAttributeField("last_name")
    phone_number = SafeAttributeField("phone_number")
    id_number = SafeAttributeField("id_number")
    birth_date = SafeAttributeField("birth_date")
    company_name = SafeAttributeField("company_name")
    company_reg_number = SafeAttributeField("company_reg_number")
    vat_id = SafeAttributeField("vat_id")
    description = SafeAttributeField("description")
    personal_tax_id = SafeAttributeField("personal_tax_id")
    identity_type = EnumAttributeField("identity_type", IdentityType)
    contact_email = SafeAttributeField("contact_email")
    external_reference_id = SafeAttributeField("external_reference_id")
    created_at = SafeAttributeField("created_at")
    verified = SafeAttributeField("verified")

    country = RelationField("country")

    class Meta:
        type = "identities"


class IdentityRepository(Repository):
    _resource_class = Identity
    _path = "identities"
