from pyteal import *

def approval_program():
    
    task_creator = Bytes("creator")
    agent = Bytes("agent")
    result_hash = Bytes("result_hash")
    verified = Bytes("verified")
    payment_amount = Bytes("amount")

   
    on_create = Seq([
        App.globalPut(task_creator, Txn.sender()),
        App.globalPut(payment_amount, Int(0)),  
        App.globalPut(verified, Int(0)),
        Approve()
    ])

   
    register_task = Seq([
        Assert(Txn.application_args.length() >= Int(2)),  
        App.globalPut(result_hash, Txn.application_args[1]),
        App.globalPut(agent, Txn.sender()),
        App.globalPut(verified, Int(0)),
        Approve()
    ])

    
    set_payment = Seq([
        Assert(Txn.sender() == App.globalGet(task_creator)),  
        Assert(Txn.application_args.length() >= Int(2)),
        App.globalPut(payment_amount, Btoi(Txn.application_args[1])),  
        Approve()
    ])

    
    approve_and_release = Seq([
        Assert(Txn.sender() == App.globalGet(task_creator)),  
        Assert(App.globalGet(verified) == Int(0)),  
        Assert(App.globalGet(payment_amount) > Int(0)),  
        App.globalPut(verified, Int(1)),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.Payment,
            TxnField.amount: App.globalGet(payment_amount),
            TxnField.receiver: App.globalGet(agent),
            
        }),
        InnerTxnBuilder.Submit(),
        Approve()
    ])

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.application_args[0] == Bytes("register_task"), register_task],
        [Txn.application_args[0] == Bytes("set_payment"), set_payment],
        [Txn.application_args[0] == Bytes("approve_and_release"), approve_and_release],
    )

    return program

def clear_state_program():
    return Approve()

if __name__ == "__main__":
    
    approval_teal = compileTeal(approval_program(), mode=Mode.Application, version=6)
    
    
    clear_teal = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
    
    
    with open("approval.teal", "w") as f:
        f.write(approval_teal)
    
    with open("clear.teal", "w") as f:
        f.write(clear_teal)
    

