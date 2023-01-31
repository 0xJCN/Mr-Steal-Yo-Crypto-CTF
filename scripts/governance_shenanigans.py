from ape import accounts, project
from .utils.helper import w3

ATTACKER_TOKEN_BALANCE = w3.to_wei(500, "ether")
GOV_TOKEN_BALANCE = w3.to_wei(2000, "ether")


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    admin = accounts.test_accounts[0]
    admin_user = accounts.test_accounts[1]
    attacker = accounts.test_accounts[2]
    o1 = accounts.test_accounts[3]
    o2 = accounts.test_accounts[4]

    print(
        f"\n--- \nOur players:\n⇒ Admin: {admin}\n⇒ Admin User: {admin_user}\n⇒ Attacker: {attacker}\n---\n"
    )
    # setting up governance token
    print("\n--- Deploying Governance Token ---\n")
    gov_token = project.NotSushiToken.deploy(sender=admin)

    # attacker sybil attack - got 3 controlled addresses WLed
    print("\n--- Setting up governance ---\n")
    gov_token.addWledAddresses(
        [admin_user.address, attacker.address, o1.address, o2.address],
        sender=admin,
    )

    gov_token.mint(admin_user.address, GOV_TOKEN_BALANCE, sender=admin)
    gov_token.mint(attacker.address, ATTACKER_TOKEN_BALANCE, sender=admin)

    # admin user delegates all votes to himself
    print("\n--- Admin user is delegating all votes to himself ---\n")
    gov_token.delegate(admin_user.address, sender=admin_user)

    # define initial votes for admin user and attacker
    user_initial_votes = gov_token.getCurrentVotes(admin_user.address) / 10**18
    attacker_initial_votes = gov_token.getCurrentVotes(attacker.address) / 10**18

    print(
        f"\n--- \nInitial Votes:\n⇒ Admin User: {user_initial_votes}\n⇒ Attacker: {attacker_initial_votes}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print("\n--- After expoit: attacker gets more delegated votes than adminUser ---\n")

    # define ending votes for admin user and attacker
    user_ending_votes = gov_token.getCurrentVotes(admin_user.address) / 10**18
    attacker_ending_votes = gov_token.getCurrentVotes(attacker.address) / 10**18

    print(
        f"\n--- \nFinal Votes:\n⇒ Admin User: {user_ending_votes}\n⇒ Attacker: {attacker_ending_votes}\n---\n"
    )

    admin_user_count = gov_token.getCurrentVotes(admin_user.address)
    attacker_count = gov_token.getCurrentVotes(attacker.address)
    assert attacker_count > admin_user_count

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
