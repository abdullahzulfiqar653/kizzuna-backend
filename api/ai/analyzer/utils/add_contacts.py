import re

from api.models.contact import Contact
from api.models.organization import Organization


def extract_domain(email):
    return email.split("@")[1].split(".")[0]


def extract_username(email):
    return email.split("@")[0]


def map_to_email(name, emails):
    words = re.findall(r"\w{3,}", name.lower())
    max_match = 0
    tie = True
    for email in emails:
        username = extract_username(email)
        match = sum(word in username for word in words)
        if match == max_match:
            tie = True
        if match > max_match:
            tie = False
            max_match = match
            best_email = email
    if not tie and max_match / len(words) > 0.4:
        # This corresponse to 1/2, 2/3, 2/4, 3/4...
        return best_email
    return None


def create_organizations(note, domains) -> dict:
    """
    Create organizations based on the given note and domains.

    :param note: The note to create the organizations for.
    :param domains: The domains to create the organizations for.
    :return: The organizations created. The key is the domain and the value is the organization.
    """

    organizations_to_create = [
        Organization(
            name=domain,
            project=note.project,
        )
        for domain in domains
    ]
    Organization.objects.bulk_create(organizations_to_create, ignore_conflicts=True)
    organizations = {
        organization.name: organization
        for organization in Organization.objects.filter(
            project=note.project, name__in=domains
        )
    }
    return organizations


def populate_participant_emails(participants, emails):
    """
    Populate the emails of the given participants.

    :param participants: The participants to populate the emails for.
    :param emails: The emails to populate the participants with.
    :return: The participants populated with the emails.
    """
    for participant in participants:
        if participant.get("name"):
            participant["email"] = map_to_email(participant["name"], emails)
    return participants


def create_contacts(note, created_by, attendees, participants, organizations):
    """
    Create contacts for the given attendees and participants.

    :param note: The note to create the contacts for.
    :param created_by: The user who created the contacts.
    :param attendees: The attendees to create the contacts for.
    :param participants: The participants to create the contacts for.
    :param organizations: The organizations to create the contacts for.
    :return: The contacts created. The key is the email and the value is the contact.
    """
    contacts_to_create = {
        attendee.email: Contact(
            name=attendee.name,
            email=attendee.email,
            organization=organizations[extract_domain(attendee.email)],
            project=note.project,
            created_by=created_by,
        )
        for attendee in attendees
    } | {
        participant["email"]: Contact(
            name=participant["name"],
            email=participant["email"],
            organization=organizations[extract_domain(participant["email"])],
            project=note.project,
            created_by=created_by,
        )
        for participant in participants
        if participant.get("email")
    }
    Contact.objects.bulk_create(contacts_to_create.values(), ignore_conflicts=True)
    contacts = {
        contact.email: contact
        for contact in Contact.objects.filter(
            project=note.project, email__in=contacts_to_create.keys()
        )
    }
    return contacts


def create_attendee_contacts(attendees, contacts):
    """
    Create attendee contacts for the given attendees.

    :param attendees: The attendees to create the contacts for.
    :param contacts: The contacts to create the attendee contacts for.
    """
    attendee_contacts_to_create = [
        attendee.contacts.through(
            contact_id=contacts[attendee.email].id,
            googlecalendarattendee_id=attendee.id,
        )
        for attendee in attendees
    ]
    Contact.attendees.through.objects.bulk_create(
        attendee_contacts_to_create, ignore_conflicts=True
    )


def add_contacts(note, created_by):
    if (
        not hasattr(note.recall_bot, "event")
        or not note.recall_bot.event.attendees.exists()
    ):
        return
    attendees = note.recall_bot.event.attendees.all()
    participants = note.recall_bot.meeting_participants
    emails = attendees.values_list("email", flat=True)
    domains = set(map(extract_domain, emails))

    organizations = create_organizations(note, domains)
    participants = populate_participant_emails(participants, emails)
    contacts = create_contacts(note, created_by, attendees, participants, organizations)
    note.organizations.set(organizations.values())
    note.contacts.set(contacts.values())
    create_attendee_contacts(attendees, contacts)
