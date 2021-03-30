"""Example steps implementation."""

from behave import given, then, when
from behave.runner import Context

import sentiment_flanders


@given("I am logged in")
def step_log_in(context: Context) -> None:
    """Log in."""
    context.logged_in = True


@when("I send a message to {person_name}")
def step_send_message(context: Context, person_name: str) -> None:
    """Send a message to a person."""
    assert context.logged_in, "You must be logged in before you can send a message"
    assert " " in person_name, "Person should have a first and last name"
    context.message_addressee = person_name
    context.message = sentiment_flanders.__name__


@then("The person {person_name} should receive a message")
def step_check_message(context: Context, person_name: str) -> None:
    """Check if the given person received a message."""
    assert context.message_addressee == person_name, "Person didn't receive a message"
