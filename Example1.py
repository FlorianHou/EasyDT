from EasyDT.Core import Template
from EasyDT.Core import CreateComponent
from EasyDT.Core import ModifyComponent
from EasyDT.Tools import Model3D
from EasyDT.Tools import CreateDB

if __name__ == "__main__":
    import glob
    import uuid
    import pprint
    from pathlib import Path

    # Initialisierung der Datenbank
    __client = CreateDB(port=27020).overwriteAndCreate()
    print(__client.list_database_names)
    __client.close()

    # Eine Liste von Pfaden zu Vorlagendateien erhalten
    fileList = glob.glob("./otherThings/*.json")
    for file in fileList:
        # Erstellen einer Vorlageninstanz
        tempalte = Template(port=27020)
        # Laden von Dateien in die Instanz
        tempalte.loads(file)
        # Abrufen des Pfads zur 3D-Modelldatei
        glbFilePath = file.replace(".json", ".glb")
        if Path(glbFilePath).exists():
            # Python-Instanz für die Erstellung eines 3D-Modells
            GlbFile = Model3D().loadFromFile(Path(file.replace(".json", ".glb")))
            # Laden von Vorlagen der base64-kodierte Modelldatei
            tempalte.set3DModel(GlbFile)
        # Hochladen auf Datenbank mit id
        insert_id = tempalte.push2Mongo(
            docId=uuid.uuid4(),
        )
        # pprint.pprint(Template(port=27020).loadFromDB(id=insert_id).getTF())

    # load a "optical.lightSource.diode" from TemplateDB
    # Create a new Component
    componentDiode = CreateComponent(port=27020).loadFromDB(
        collName="Templates",
        templateName="Template_L375P70MLD",
    )
    # Hochladen der Produktion in die Datenbank
    DiodeInsert_id = componentDiode.push2Mongo(docId=uuid.uuid4())
    print(f"DiodeInsert_id:{DiodeInsert_id}")

    # load a "optical.lightSource.mount.submount" from Tempalate DB
    # Create a sub mount
    componentSubMount = CreateComponent(port=27020).loadFromDB(
        collName="Templates", templateName="Template_Submount_10001"
    )
    print(componentSubMount)
    SubMountInsert_Id = componentSubMount.push2Mongo(docId=str(uuid.uuid4()))
    print(SubMountInsert_Id)

    # load a "optical.lightSource.mount.sub"
    # Create a Sub1001
    componentSub = CreateComponent(port=27020).loadFromDB(
        collName="Templates", templateName="Template_Sub_10001"
    )
    print(componentSub)
    componentsList = [
        ModifyComponent(port=27020).autoCreateOneChild(componentId=SubMountInsert_Id),
        ModifyComponent(port=27020).autoCreateOneChild(componentId=DiodeInsert_id),
    ]
    ## Manuelle Erstellung von Unterteillisten
    # componentsList = [
    #     {
    #         "_id": SubMountInsert_Id,
    #         "componentName": CreateComponent(port=27020).loadFromDB(
    #             id=SubMountInsert_Id, collName="Productions"
    #         )["componentName"],
    #         "templateName": CreateComponent(port=27020).loadFromDB(
    #             id=SubMountInsert_Id, collName="Productions"
    #         )["templateName"],
    #         "templateid": CreateComponent(port=27020).loadFromDB(
    #             id=SubMountInsert_Id, collName="Productions"
    #         )["templateId"],
    #     },
    #     {
    #         "_id": DiodeInsert_id,
    #         "componentName": CreateComponent(port=27020).loadFromDB(
    #             id=DiodeInsert_id, collName="Productions"
    #         )["componentName"],
    #         "templateName": CreateComponent(port=27020).loadFromDB(
    #             id=DiodeInsert_id, collName="Productions"
    #         )["templateName"],
    #         "templateid": CreateComponent(port=27020).loadFromDB(
    #             id=DiodeInsert_id, collName="Productions"
    #         )["templateId"],
    #     },
    # ]
    componentSub.fillAllChilds(componentsList, matchKey="componentName")
    SubInsert_Id = componentSub.push2Mongo(docId=uuid.uuid4())
    print(SubInsert_Id)
    print(
        CreateComponent(port=27020).loadFromDB(id=SubInsert_Id, collName="Productions")
    )
    pprint.pprint(componentSub.searchAllChilds())

    # -------------------------------------------
    # load a "optical.lightSource.lens.BiConcave"
    # Create a LD2746
    componentLD2746_1 = CreateComponent(port=27020).loadFromDB(
        collName="Templates", templateName="Template_LD2746"
    )
    print(componentSubMount)
    LD2746_1_Id = componentLD2746_1.push2Mongo(docId=str(uuid.uuid4()))
    print(LD2746_1_Id)

    # load a "optical.lightSource.lens.BiConcave"
    # Create a LD2746
    componentLD2746_2 = CreateComponent(port=27020).loadFromDB(
        collName="Templates", templateName="Template_LD2746"
    )
    print(componentLD2746_2)
    LD2746_2_Id = componentLD2746_1.push2Mongo(docId=str(uuid.uuid4()))
    print(LD2746_2_Id)
    # load a "optical.lightSource.lens.BiConcave"
    # Create a LA1116
    componentLA1116 = CreateComponent(port=27020).loadFromDB(
        collName="Templates", templateName="Template_LA1116-A"
    )
    print(componentLA1116)
    LA1116_Id = componentLA1116.push2Mongo(docId=str(uuid.uuid4()))
    print(LA1116_Id)

    # load a "optical.lightSource.combination"
    # Create a LS2001
    componentKombi = CreateComponent(port=27020).loadFromDB(
        collName="Templates", templateName="Template_LAS_20001"
    )
    print(componentKombi)
    componentsList = [
        CreateComponent(port=27020).autoCreateOneChild(componentId=LD2746_1_Id),
        CreateComponent(port=27020).autoCreateOneChild(componentId=LD2746_2_Id),
        CreateComponent(port=27020).autoCreateOneChild(componentId=SubInsert_Id),
        CreateComponent(port=27020).autoCreateOneChild(componentId=LA1116_Id),
    ]
    componentKombi.fillAllChilds(componentsList, matchKey="componentName")
    KombiInsert_Id = componentKombi.push2Mongo(docId=uuid.uuid4())
    print(SubInsert_Id)
    print(
        CreateComponent(port=27020).loadFromDB(
            id=KombiInsert_Id, collName="Productions"
        )
    )
    pprint.pprint(componentKombi.searchAllChilds())
