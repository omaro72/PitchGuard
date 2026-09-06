class IncompleteWorkflowError(Exception):
    def __init__(self) -> None:
        super().__init__("The reviewer workflow is incomplete, so a final decision cannot be made.")
