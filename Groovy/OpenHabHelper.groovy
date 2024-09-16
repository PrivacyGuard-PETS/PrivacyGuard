import groovy.console.ui.TreeNodeWithProperties
import groovy.json.JsonOutput
import org.codehaus.groovy.syntax.Token

import javax.swing.tree.DefaultMutableTreeNode
import javax.swing.tree.TreeNode

class OpenHabHelper {

    DefaultMutableTreeNode rootDmtn

    String filenameStr
    String descriptionStr
    Map inputMap
    List triggersList
    // list of all nodes
    List rootEnumList

    // list of all method call node
    List allMethodCallList
    // map of method call [raw_text:receiver, method, [parameters]]
    Map methodCallParamMap

    // list of all method node
    List allMethodList
    // map of method node [name:[parameters]]
    Map methodParamMap

    // list of all declaration node
    List allDeclarationList
    Map declarationParamMap

    // list of all binary node
    List allBinaryList
    Map binaryParamMap

    // Method Call to Method Node with Condition
    Map methodCallMethodNodeMap
    Map methodCallMethodNodeVarMap

    List sinkFunctionList = []
//    List commandsList = ["callScript", "executeCommandLine", "postUpdate", "publish", "publishMQTT", "pushNotification", "pushover", "pushoverBuilder", "sendBroadcastNotification", "sendCommand", "sendHABotNotification", "sendHttpDeleteRequest", "sendHttpGetRequest", "sendHttpPostRequest", "sendHttpPutRequest", "sendHttpRequest", "sendLogNotification", "sendMail", "sendNotification", "sendPriorityMessage", "sendPushoverMessage", "sendTelegram", "sendTelegramAnswer", "sendTelegramQuery", "sendTweet", "sendXbmcNotification", "sendcommand"]
    List commandsList = ["postUpdate", "pushNotification", "sendBroadcastNotification", "sendCommand", "sendHABotNotification", "sendHttpDeleteRequest", "sendHttpGetRequest", "sendHttpPostRequest", "sendHttpPutRequest", "sendHttpRequest", "sendLogNotification", "sendMail", "sendNotification", "sendPriorityMessage", "sendPushoverMessage", "sendTelegram", "sendTelegramAnswer", "sendTelegramQuery", "sendTweet", "sendXbmcNotification"]


    OpenHabHelper(DefaultMutableTreeNode rootDmtn, String filenameStr, String descriptionStr, Map inputMap, List triggersList) {
        this.rootDmtn = rootDmtn
        this.filenameStr = filenameStr
        this.descriptionStr = descriptionStr
        this.inputMap = inputMap
        this.triggersList = triggersList

        // Get list of all nodes in the app
        rootEnumList = rootDmtn.depthFirstEnumeration().toList()

        // Get all method call node, remove some useless nodes, include definition, subscribe and so on
        allMethodCallList = getAllTnwpNodesList(rootEnumList, "MethodCall")
        methodCallParamMap = getMethodCallParamMap()

        // Get all method node
        allMethodList = getAllTnwpNodesList(rootEnumList, "MethodNode")
        methodParamMap = getMethodParamMap()

        // Get all declaration expression node
        allDeclarationList = getAllTnwpNodesList(rootEnumList, "Declaration")
        declarationParamMap = getDeclarationParamMap()

        // Get all binary expression node
        allBinaryList = getAllTnwpNodesList(rootEnumList, "Binary")
        binaryParamMap = getBinaryParamMap()

        methodCallMethodNodeMap = [:]
        methodCallMethodNodeVarMap = [:]

    }

    /**
     * Get all the information from root node
     * @param rootDmtn : root node
     * @return all the necessary information in the app
     */
    Map getInformation() {
        for (TreeNodeWithProperties nodeTnwp : allMethodCallList) {

            String methodCallTextStr = getTnwpText(nodeTnwp)

            def (String receiverStr, String methodStr, List argumentsList) = methodCallParamMap[methodCallTextStr]

            if (commandsList.contains(methodStr)) {
                def (String nameMethodStr, List condList) = getPathFromMethodCallToMethod(nodeTnwp)

                if (!(methodCallMethodNodeMap.containsKey(methodCallTextStr))) {
                    methodCallMethodNodeMap[methodCallTextStr] = [:]
                }
                if (!(methodCallMethodNodeMap[methodCallTextStr].containsKey(nameMethodStr))) {
                    methodCallMethodNodeMap[methodCallTextStr][nameMethodStr] = []
                }
                methodCallMethodNodeMap[methodCallTextStr][nameMethodStr] << condList

//                String methodCallReplTextStr = getMethodCallReplaceParamMap(nodeTnwp, methodParamMap[nameMethodStr])
//                if (closureTnwpMap.containsKey(nodeTnwp)) {
//                    def (String parentRecvStr, String closureTextStr) = closureTnwpMap[nodeTnwp]
//                    List methodCallParamsList = methodCallParamMap[methodCallReplTextStr]
//
//                    methodCallReplTextStr = closureTextStr
//                    methodCallParamsList[0] = parentRecvStr
//                    methodCallParamMap[methodCallReplTextStr] = methodCallParamsList
//                }
////                def (List condCleanList, List condVarCleanList) = getUniqueCondPath(nameMethodStr, condList, condVarTnwpList)
//
//                if (!(methodCallMethodNodeMap.containsKey(methodCallReplTextStr))) {
//                    methodCallMethodNodeMap[methodCallReplTextStr] = [:]
//                    methodCallMethodNodeVarMap[methodCallReplTextStr] = [:]
//                }
//                if (!(methodCallMethodNodeMap[methodCallReplTextStr].containsKey(nameMethodStr))) {
//                    methodCallMethodNodeMap[methodCallReplTextStr][nameMethodStr] = []
//                    methodCallMethodNodeVarMap[methodCallReplTextStr][nameMethodStr] = []
//                }
//                methodCallMethodNodeMap[methodCallReplTextStr][nameMethodStr] << condList
//                methodCallMethodNodeVarMap[methodCallReplTextStr][nameMethodStr] << condVarTnwpList
////                methodCallMethodNodeMap[methodCallReplTextStr][nameMethodStr] << condCleanList
////                methodCallMethodNodeVarMap[methodCallReplTextStr][nameMethodStr] << condVarCleanList
            }

        }


        Map infoMap = [
                "filenameStr"            : filenameStr,
                "descriptionStr"         : descriptionStr,
                "triggersList"           : triggersList,
                "inputMap"               : inputMap,
                "declarationMap"         : declarationParamMap,
                "binaryMap"              : binaryParamMap,
                "methodParamMap"         : methodParamMap,
                "methodCallParamMap"     : methodCallParamMap,
                "methodCallMethodNodeMap": methodCallMethodNodeMap,
//                "methodCallMethodNodeVarMap": methodCallMethodNodeVarMap
        ]
        return infoMap
    }

    /**
     * Get detail from declaration node
     * @return map of declaration node and parameter, [left:[right parameters]]
     */
    List getDetailFromDeclarationNode(TreeNodeWithProperties nodeTnwp) {
        DefaultMutableTreeNode leftNodeTnwp = nodeTnwp.getFirstChild()
        String leftStr = getTnwpText(leftNodeTnwp)
        String binaryStr = ""
        if (nodeTnwp.childCount > 1) {
            DefaultMutableTreeNode rightNodeTnwp = nodeTnwp.getChildAt(1)
            binaryStr = getTnwpText(rightNodeTnwp)
        }
        return [leftStr, binaryStr]
    }


    /**
     * Generate map of declaration node and parameter
     * @return map of declaration node and parameter, [left:[right parameters]]
     */
    Map getDeclarationParamMap() {
        Map declarationParamMap = [:]
        allDeclarationList.each {
            it ->
                def (String leftStr, String binaryStr) = getDetailFromDeclarationNode(it)
                declarationParamMap[leftStr] = binaryStr
        }
        return declarationParamMap
    }


    /**
     * Get detail from declaration node
     * @return map of declaration node and parameter, [left:[right parameters]]
     */
    List getDetailFromBinaryNode(TreeNodeWithProperties nodeTnwp) {

        Token operToken = getProperty(nodeTnwp, "operation")
        String firstOperStr = operToken.properties["text"]

        if (firstOperStr == "=") {
            def (String leftStr, String binaryStr) = getDetailFromDeclarationNode(nodeTnwp)
            declarationParamMap[leftStr] = binaryStr
            return [null, null]
        }

        String binaryStr = getBinaryExpression(nodeTnwp)

        DefaultMutableTreeNode leftNodeTnwp = nodeTnwp.getFirstChild()
        String leftStr = getTnwpText(leftNodeTnwp)
        DefaultMutableTreeNode rightNodeTnwp = nodeTnwp.getChildAt(1)
        String rightStr = getTnwpText(rightNodeTnwp)

        return [binaryStr, [leftStr, firstOperStr, rightStr]]
    }


    /**
     * Generate map of declaration node and parameter
     * @return map of declaration node and parameter, [left:[right parameters]]
     */
    Map getBinaryParamMap() {
        Map binaryParamMap = [:]
        allBinaryList.each {
            it ->
                def (String nameStr, List paramList) = getDetailFromBinaryNode(it)
                if (nameStr != null) {
                    binaryParamMap[nameStr] = paramList
                }
        }
        return binaryParamMap
    }


    /**
     * Generate map of method node and parameter
     * @return map of method node and parameter, [name:[parameters]]
     */
    Map getMethodParamMap() {
        Map methodParamMap = [:]
        allMethodList.each {
            it ->
                def (String nameStr, List paramList) = getDetailFromMethodNode(it)
                methodParamMap[nameStr] = paramList
        }
        return methodParamMap
    }


    /**
     * Generate map of method call node and parameter
     * @return map of method node, receiver and parameter, [raw_text:receiver, method, [parameters]]
     */
    Map getMethodCallParamMap() {
        Map methodCallParamMap = [:]
        allMethodCallList.each {
            it ->
                def (String receiverStr, String methodStr, List argumentsList) = getDetailFromMethodCallNode(it)
                String methodCallTextStr = getTnwpText(it)
                methodCallParamMap[methodCallTextStr] = [receiverStr, methodStr, argumentsList]
        }
        return methodCallParamMap
    }

    /**
     * Get condition path from method call expression to method node
     * @param nodeTnwp : method call expression
     * @return the name of the method node, the condition path with text string, the condition path with variable tnwp node
     */
    List getPathFromMethodCallToMethod(TreeNodeWithProperties nodeTnwp) {
        TreeNode[] rawPathArr = nodeTnwp.getPath()
        String nameMethodStr = "run"
        List condList = []

        for (int iInt = 0; iInt < rawPathArr.size(); iInt++) {
            if (!(rawPathArr[iInt] instanceof TreeNodeWithProperties)) {
                continue
            }

            TreeNodeWithProperties rawNodeDmtn = (TreeNodeWithProperties) rawPathArr[iInt]
            String nodeClassStr = getTnwpString(rawNodeDmtn)

            if (nodeClassStr.startsWith("MethodNode")) {
                nameMethodStr = getTnwpName(rawNodeDmtn)
            } else if (nodeClassStr in ["IfStatement", "CaseStatement", "SwitchStatement", "ForStatement"]) {
                if (nodeClassStr == "IfStatement") {
                    if (rawPathArr[iInt + 1] == rawNodeDmtn.getChildAt(1)) {
                        condList << getTnwpText(rawNodeDmtn.getFirstChild())
                    } else {
                        condList << "#" + getTnwpText(rawNodeDmtn.getFirstChild())
                    }
                }

            }
        }

        return [nameMethodStr, condList]
    }


    /**
     * Get condition path from method call expression to method node
     * @param nodeTnwp : method call expression
     * @return the name of the method node, the condition path with text string, the condition path with variable tnwp node
     */
//    List getPathFromMethodCallToMethod(TreeNodeWithProperties nodeTnwp) {
//
//        List condList = []
//        List condVarTnwpList = []
//
//        TreeNodeWithProperties prevTnwp = null
//
//        while (true) {
//            TreeNodeWithProperties firstTnwp = null
//            List<TreeNodeWithProperties> notTnwpList = []
//            List<TreeNodeWithProperties> varTnwpList = []
//            List<String> binaryStrTnwpList = []
//
//            if (getTnwpString(nodeTnwp) in ["IfStatement", "CaseStatement", "SwitchStatement", "ForStatement"]) {
//                firstTnwp = nodeTnwp.getFirstChild()
//
//                notTnwpList = firstTnwp.depthFirstEnumeration().findAll { it ->
//                    getTnwpString(it).startsWith("Not")
//                }
//
//                varTnwpList = firstTnwp.depthFirstEnumeration().findAll { it ->
//                    getTnwpString(it).startsWith("Variable")
//                }
//
//                for (varTnwp in varTnwpList) {
//                    String varText = getTnwpText(varTnwp)
//                    if (inputMap.containsKey(varText) || varText in ["evt", "location"]) {
////                        if(inputMap[varText][0].startsWith("capability")){
////                            String binaryText = getBinaryExpression(varTnwp)
//                        if (inputMap.containsKey(varText) && !inputMap[varText][0].startsWith("capability")) {
//                            continue
//                        }
//                        String binaryText = getBinaryExpression(varTnwp)
////                            String binaryText = getNearestBinaryExpression(varTnwp)
//                        if (binaryText != "") {
//                            binaryStrTnwpList << binaryText
//                        }
////                        }
//                    } else if (varText == "this") {
//                        String thisText = getMethodExpression(varTnwp)
//                        if (thisText != "") {
//                            binaryStrTnwpList << thisText
//                        }
//
//                    } else {
////                        TreeNodeWithProperties temp = getPossibleDeclareBinaryExpr(varTnwp, [])
//                        binaryStrTnwpList << varText
////                        print()
//                    }
//                }
//            }
//
//            if (getTnwpString(nodeTnwp).equals("IfStatement")) {
//                List ifChildrenList = nodeTnwp.children().toList()
//
//                if (getTnwpString(prevTnwp).startsWith("BlockStatement")) {
//                    String textStr = getTnwpText(firstTnwp)
//
//                    if (notTnwpList.size() > 0) {
//                        textStr = "#Not#" + textStr
//                    }
//                    if (ifChildrenList.size() == 3 && ifChildrenList[2] == prevTnwp) {
//                        textStr = "#Else#" + textStr
//                    }
//
//                    condList << textStr
////                    condVarTnwpList << varTnwpList
//                    condVarTnwpList << binaryStrTnwpList
//                }
//            } else if (getTnwpString(nodeTnwp) in ["CaseStatement", "SwitchStatement"]) {
//
//                String textStr = getTnwpText(firstTnwp)
//                if (notTnwpList.size() > 0) {
//                    textStr = "#Not#" + textStr
//                }
//
//                if (getTnwpString(nodeTnwp).equals("SwitchStatement")) {
//                    textStr = "#Switch#" + textStr
//                } else {
//                    textStr = "#Case#" + textStr
//                }
//
//                condList << textStr
////                condVarTnwpList << varTnwpList
//                condVarTnwpList << binaryStrTnwpList
//            } else if (getTnwpString(nodeTnwp) in ["ForStatement"]) {
//
//                String textStr = getTnwpText(firstTnwp)
//
//                textStr = "#For#" + textStr
//
//                condList << textStr
////                condVarTnwpList << varTnwpList
//                condVarTnwpList << binaryStrTnwpList
//            }
//
//            prevTnwp = nodeTnwp
//            if (getTnwpString(nodeTnwp.getParent()).equals("Body")) {
//                break
//            }
//
//            if (getTnwpString(nodeTnwp.getParent()).equals("root")) {
//                condList = condList.reverse()
//                condVarTnwpList = condVarTnwpList.reverse()
//                return ["root", condList, condVarTnwpList]
//            }
//
//            nodeTnwp = nodeTnwp.getParent()
//        }
//        condList = condList.reverse()
//        condVarTnwpList = condVarTnwpList.reverse()
//
//        // MethodNode, Conditions
//        nodeTnwp = nodeTnwp.getParent().getParent()
//        String nameMethodStr = getTnwpName(nodeTnwp)
//        return [nameMethodStr, condList, condVarTnwpList]
//    }

    def getUniqueCondPath(String nameMethodStr, List condList, List condVarTnwpList) {
        List condCleanList = []
        List condVarCleanList = []

        List argumentList = methodParamMap[nameMethodStr]
        int condSizeInt = condList.size()

        for (int iInt = 0; iInt < condSizeInt; iInt++) {
            List varsList = condVarTnwpList[iInt]
            Set<String> binaryExprSet = []
            for (TreeNodeWithProperties varTnwp : varsList) {
                String varTextStr = getTnwpText(varTnwp)

                String nearestBinaryStr = getNearestBinaryExpression(varTnwp)
                def (String capOrEventStr, String capaOrEventRightExprStr) = getVariableCapaOrEvent(varTnwp, argumentList, null)

                if (capOrEventStr != null &&
                        nearestBinaryStr != null &&
                        ((nearestBinaryStr.contains("==")) ||
                                (nearestBinaryStr.contains(">")) ||
                                (nearestBinaryStr.contains("<")) ||
                                (nearestBinaryStr.contains("!=")))) {
//                    println("${getTnwpText(varTnwp)}:${capOrEventStr}:${nearestBinaryStr}")
                    // replace the binary string
                    nearestBinaryStr = nearestBinaryStr.replace(varTextStr, capaOrEventRightExprStr)
                    binaryExprSet << nearestBinaryStr
                } else if (capOrEventStr != null && nearestBinaryStr == null) {
                    binaryExprSet << capaOrEventRightExprStr
                }
            }
            if (binaryExprSet.size() > 0) {
                condCleanList << condList[iInt]
                condVarCleanList << binaryExprSet.sort()
            }
        }
        return [condCleanList, condVarCleanList]
    }

    String getBinaryExpression(DefaultMutableTreeNode tnwpNode) {
        while (!getTnwpString(tnwpNode).startsWith("Binary")) {
            if (getTnwpString(tnwpNode).startsWith("Body")) {
                return ""
            }
            tnwpNode = tnwpNode.parent
        }
        return getTnwpText(tnwpNode)
    }

    String getMethodExpression(DefaultMutableTreeNode tnwpNode) {
        while (!getTnwpString(tnwpNode).startsWith("MethodCall")) {
            if (getTnwpString(tnwpNode).startsWith("Body")) {
                return ""
            }
            tnwpNode = tnwpNode.parent
        }
        return getTnwpText(tnwpNode)
    }

    TreeNodeWithProperties getPossibleDeclareBinaryExpr(TreeNodeWithProperties varTnwp, List argumentList) {
        String rightExprStr = null

        String varTextStr = getTnwpText(varTnwp)
        if (inputMap.containsKey(varTextStr)
                || (varTextStr in argumentList)
                || (varTextStr in ["location"])) {
            return varTnwp
        }
        DefaultMutableTreeNode currDmtn = expressionToStatement(varTnwp)
        while (currDmtn != null) {
            DefaultMutableTreeNode prevDmtn = currDmtn.getPreviousSibling()
            if (prevDmtn == null) {
                currDmtn = currDmtn.getParent()
                while (currDmtn != null && getTnwpString(currDmtn).startsWith("BlockStatement")) {
                    currDmtn = currDmtn.getParent()
//                    println(currDmtn)
                }
            } else {
                if (getTnwpString(prevDmtn) in ["ExpressionStatement - BinaryExpression", "ExpressionStatement - DeclarationExpression"]) {
                    TreeNodeWithProperties expressionTnwp = prevDmtn.getFirstChild()
                    TreeNodeWithProperties leftTnwp = expressionTnwp.getFirstChild()
                    TreeNodeWithProperties rightTnwp = expressionTnwp.getLastChild()

                    String leftTextStr = getTnwpText(leftTnwp)
                    String rightClassStr = getTnwpString(rightTnwp)
                    String rightTextStr = getTnwpText(rightTnwp)
                    if (leftTextStr.equals(varTextStr)) {
                        return rightTnwp
                    }
                }
                currDmtn = prevDmtn
            }

        }

        return varTnwp
    }

    /**
     * Get condition path from method call expression to method node
     * @param nodeTnwp : method call expression
     * @return the name of the method node, the condition path with text string, the condition path with variable tnwp node
     */

    Object getProperty(TreeNodeWithProperties tnwpNode, String propertyName) {
        List<List> propertiesList = tnwpNode.getProperties()
        for (List itemList : propertiesList) {
            if (itemList[0] == propertyName) {
                return itemList[3]
            }
        }
        return null
    }

    /**
     *
     * @param currStr
     * @return
     */
    String convertDeviceCommand() {
        // currentValue()
        // currentState()
        // <attribute name>State
        List regexPatternList = [/(\w+).currentValue\((\w+)\)/, /(\w+).currentState\((\w+)\)/, /(\w+).(\w+)State$/]
        for (String regexPatternStr : regexPatternList) {
            if (currStr ==~ regexPatternStr) {
                return currStr.replaceAll(regexPatternStr, '$1.$2')
            }
        }
        // current<Uppercase attribute name>
        String upperPatternStr = /(\w+).current([A-Z]\w*)/
        if (currStr ==~ upperPatternStr) {
            currStr = currStr.replaceAll(upperPatternStr, '$1#$2')
            List tempList = currStr.split("#")
            tempList[1] = tempList[1][0].toLowerCase() + tempList[1][1..-1]
            return tempList.join(".")
        }
        return currStr
    }

    /**
     * Get the [location, state], capability or event related to the variable node
     * @param varTnwp : variable node
     * @return [location, state], capability or event related to the variable node
     */
    List getVariableCapaOrEvent(TreeNodeWithProperties varTnwp, List argumentList, String exprStr) {
        String capaOrEventStr = null
        String capaOrEventRightExprStr = null

        String varTextStr = getTnwpText(varTnwp)
        // oauth_controller[imbrianj@oauth_controller].groovy
        if ((inputMap.containsKey(varTextStr) && inputMap[varTextStr][0].startsWith("capability"))
                || (varTextStr in argumentList)
                || (varTextStr in ["location"])) {
            if (exprStr == null) {
                return [varTextStr, convertDeviceCommand(varTextStr)]
            }
            return [varTextStr, convertDeviceCommand(exprStr)]
        }
        DefaultMutableTreeNode currDmtn = expressionToStatement(varTnwp)
        while (currDmtn != null) {
            DefaultMutableTreeNode prevDmtn = currDmtn.getPreviousSibling()
            if (prevDmtn == null) {
                currDmtn = currDmtn.getParent()
                while (currDmtn != null && getTnwpString(currDmtn).startsWith("BlockStatement")) {
                    currDmtn = currDmtn.getParent()
//                    println(currDmtn)
                }
            } else {
                if (getTnwpString(prevDmtn) in ["ExpressionStatement - BinaryExpression", "ExpressionStatement - DeclarationExpression"]) {
                    TreeNodeWithProperties expressionTnwp = prevDmtn.getFirstChild()
                    TreeNodeWithProperties leftTnwp = expressionTnwp.getFirstChild()
                    TreeNodeWithProperties rightTnwp = expressionTnwp.getLastChild()

                    String leftTextStr = getTnwpText(leftTnwp)
                    String rightClassStr = getTnwpString(rightTnwp)
                    String rightTextStr = getTnwpText(rightTnwp)
                    if (leftTextStr.equals(varTextStr)) {
                        if (rightClassStr.startsWith("Variable")) {
                            return getVariableCapaOrEvent(rightTnwp, argumentList, rightTextStr)
                        } else if (rightClassStr.startsWith("MethodCall")) {
                            return getVariableCapaOrEvent(rightTnwp.getFirstChild(), argumentList, rightTextStr)
                        } else if (rightClassStr.startsWith("Cast")) {
                            if (rightTnwp.childCount == 1) {
                                TreeNodeWithProperties castChildTnwp = rightTnwp.getFirstChild()
                                String castChildClassStr = getTnwpString(castChildTnwp)
                                String castChildTextStr = getTnwpText(castChildTnwp)
                                if (castChildClassStr.startsWith("Property")) {
                                    return getVariableCapaOrEvent(castChildTnwp.getFirstChild(), argumentList, castChildTextStr)
                                } else if (castChildClassStr.startsWith("Variable")) {
                                    return getVariableCapaOrEvent(castChildTnwp, argumentList, castChildTextStr)
                                } else {
                                    println("Cast: Type Error")
                                }
                            } else {
                                println("Cast: Child Count Error")
                            }
                        } else if (rightClassStr.startsWith("Binary") || rightClassStr.startsWith("Property")) {
                            return [varTextStr, rightTextStr]
                        } else {
                            println("${rightClassStr} >> ${rightTextStr} >> Not Implemented")
//                            return [varTextStr, varTextStr]
//                            println(rightClassStr)
//                            println(getTnwpText(rightTnwp))
                        }
                    }
                }
                currDmtn = prevDmtn
            }

        }

        return [capaOrEventStr, convertDeviceCommand(capaOrEventRightExprStr)]
    }

    /**
     * Get the [location, state], capability or event related to the variable node
     * @param varTnwp : variable node
     * @return [location, state], capability or event related to the variable node
     */
    String getNearestDeclareBinaryExpr(TreeNodeWithProperties varTnwp, List argumentList) {
        String rightExprStr = null

        String varTextStr = getTnwpText(varTnwp)
        if (inputMap.containsKey(varTextStr)
                || (varTextStr in argumentList)
                || (varTextStr in ["location"])) {
            return varTextStr
        }
        DefaultMutableTreeNode currDmtn = expressionToStatement(varTnwp)
        while (currDmtn != null) {
            DefaultMutableTreeNode prevDmtn = currDmtn.getPreviousSibling()
            if (prevDmtn == null) {
                currDmtn = currDmtn.getParent()
                while (currDmtn != null && getTnwpString(currDmtn).startsWith("BlockStatement")) {
                    currDmtn = currDmtn.getParent()
//                    println(currDmtn)
                }
            } else {
                if (getTnwpString(prevDmtn) in ["ExpressionStatement - BinaryExpression", "ExpressionStatement - DeclarationExpression"]) {
                    TreeNodeWithProperties expressionTnwp = prevDmtn.getFirstChild()
                    TreeNodeWithProperties leftTnwp = expressionTnwp.getFirstChild()
                    TreeNodeWithProperties rightTnwp = expressionTnwp.getLastChild()

                    String leftTextStr = getTnwpText(leftTnwp)
                    String rightClassStr = getTnwpString(rightTnwp)
                    String rightTextStr = getTnwpText(rightTnwp)
                    if (leftTextStr.equals(varTextStr)) {
                        return rightTextStr
                    }
                }
                currDmtn = prevDmtn
            }

        }

        if (rightExprStr == null) {
            rightExprStr = getTnwpText(varTnwp)
        }
        return rightExprStr
    }
    /**
     * Get the nearest statement from expression node
     * @param nodeTnwp : expression node
     * @return the nearest statement of the expression node
     */
    TreeNodeWithProperties expressionToStatement(DefaultMutableTreeNode nodeTnwp) {

        while (!getTnwpString(nodeTnwp).contains("Statement")) {
            nodeTnwp = nodeTnwp.getParent()
        }
        return nodeTnwp
    }


    /**
     * Get the nearest binary expression string for variable expression node
     * @param nodeTnwp : variable expression node
     * @return the nearest binary expression string of the variable expression node
     */
    String getNearestBinaryExpression(DefaultMutableTreeNode nodeTnwp) {

        while ((nodeTnwp != null) && (!getTnwpString(nodeTnwp).startsWith("Binary"))) {
            nodeTnwp = nodeTnwp.getParent()
        }
        String nearestBinaryStr = getTnwpText(nodeTnwp)
        if (nearestBinaryStr != null) {
            nearestBinaryStr = nearestBinaryStr - '(' - ')'
        }
        if (nodeTnwp != null && getTnwpString(nodeTnwp.getFirstChild()).startsWith("Constant")) {
            List operationsList = [" == ", " != ", " >= ", " <= ", " > ", " < "]
            for (String operationStr : operationsList) {
                if (nearestBinaryStr.contains(operationStr)) {
                    List splitBinaryList = nearestBinaryStr.split(operationStr).reverse()
                    nearestBinaryStr = splitBinaryList.join(operationStr)
                    break
                }
            }
        }

        return nearestBinaryStr
    }


    /**
     * Get detail from MethodNode
     * @param nodeTnwp : Method Node
     * @return name and parameter list of MethodNode
     */
    List getDetailFromMethodNode(TreeNodeWithProperties nodeTnwp) {
        String nameStr = getTnwpName(nodeTnwp)
        List paramList = []
        DefaultMutableTreeNode firstChild = nodeTnwp.getFirstChild()
        if (getTnwpString(firstChild).equals("Parameters")) {
            paramList = firstChild.children().collect { it ->
                getTnwpName(it)
            }
        }

        return [nameStr, paramList]
    }


    String getMethodCallReplaceParamMap(TreeNodeWithProperties nodeTnwp, List methodNodeArgumentsList) {

        def (TreeNodeWithProperties receiverTnwp, TreeNodeWithProperties methodTnwp, List argumentsTnwpList) = getDetailTnwpFromMethodCallNode(nodeTnwp)

        String receiverStr = getTnwpText(receiverTnwp)
        String methodStr = getTnwpText(methodTnwp)
        List argumentsStrList = []

        if (!(receiverStr.equals("this") && (methodStr in sinkFunctionList))) {
            return getTnwpText(nodeTnwp)
        }


        for (TreeNodeWithProperties tempTnwp : argumentsTnwpList) {
            String tempClassStr = getTnwpString(tempTnwp)
            if (tempClassStr.equals("MapEntryExpression")) {
                argumentsStrList << "${getTnwpText(tempTnwp.getFirstChild())} : ${getTnwpText(tempTnwp.getLastChild())}"
            } else if (tempClassStr.startsWith("GString") || tempClassStr.startsWith("Constant")) {
                argumentsStrList << getTnwpText(tempTnwp)
            } else {
                argumentsStrList << getNearestDeclareBinaryExpr(tempTnwp, methodNodeArgumentsList)
            }
        }

        String methodTextReplStr = receiverStr + "." + methodStr + "(" + argumentsStrList.join(", ") + ")"
        if (!methodCallParamMap.containsKey(methodTextReplStr)) {
            methodCallParamMap[methodTextReplStr] = [receiverStr, methodStr, argumentsStrList]
        }
        return methodTextReplStr
    }

    /**
     * Get detail from method call node
     * @param nodeTnwp : method call node
     * @return receiver, method and parameter list of MethodNode
     */
    List getDetailTnwpFromMethodCallNode(TreeNodeWithProperties nodeTnwp) {

        TreeNodeWithProperties receiverTnwp = nodeTnwp.getChildAt(0)
        TreeNodeWithProperties methodTnwp = nodeTnwp.getChildAt(1)
        TreeNodeWithProperties argumentTnwp = nodeTnwp.getChildAt(2)

        List argumentsTnwpList = []

        List childArguList = argumentTnwp.children().toList()
        if (getTnwpString(childArguList[0]) in ["MapExpression", "NamedArgumentListExpression"]) {
            List mapEntryList = childArguList[0].children().toList()
            for (TreeNodeWithProperties tempTnwp : mapEntryList) {
                argumentsTnwpList << tempTnwp
            }
        } else {
            if (childArguList.size() > 0) {
                argumentsTnwpList << childArguList[0]
            }
        }

        for (int idxInt = 1; idxInt < childArguList.size(); idxInt++) {
            argumentsTnwpList << childArguList[idxInt]
        }

        return [receiverTnwp, methodTnwp, argumentsTnwpList]
    }

    /**
     * Get detail from method call node
     * @param nodeTnwp : method call node
     * @return receiver, method and parameter list of MethodNode
     */
    List getDetailFromMethodCallNode(TreeNodeWithProperties nodeTnwp) {
        def (TreeNodeWithProperties receiverTnwp, TreeNodeWithProperties methodTnwp, List argumentsTnwpList) = getDetailTnwpFromMethodCallNode(nodeTnwp)

        String receiverStr = getTnwpText(receiverTnwp)
        String methodStr = getTnwpText(methodTnwp)
        List argumentsStrList = []

        for (TreeNodeWithProperties tempTnwp : argumentsTnwpList) {
            if (getTnwpString(tempTnwp).equals("MapEntryExpression")) {
                argumentsStrList << "${getTnwpText(tempTnwp.getFirstChild())} : ${getTnwpText(tempTnwp.getLastChild())}"
            } else {
                argumentsStrList << getTnwpText(tempTnwp)
            }
        }

        return [receiverStr, methodStr, argumentsStrList]
    }

    /**
     * Get all the TreeNodeWithProperty node with type typeStr from list of enumeration of node
     * @param nodeEnumList : list of enumeration of node
     * @param typeStr : type of TreeNodeWithProperty node
     * @return list of TreeNodeWithProperty node with corresponding type
     */
    List getAllTnwpNodesList(List nodeEnumList, String typeStr) {
        List nodeList = nodeEnumList.findAll {
            it ->
                getTnwpString(it).startsWith(typeStr)
        }
        return nodeList
    }


    /**
     * Get string of a TreeNodeWithProperty node (display in Groovy AST Browser),
     * e.g. MethodCall - this.preference({...})
     * @param nodeTnwp : TreeNodeWithProperty node
     * @return string of TreeNodeWithProperty node
     */
    String getTnwpString(DefaultMutableTreeNode nodeTnwp) {
        if (nodeTnwp == null) {
            return null
        }
        return nodeTnwp.toString()
    }


    /**
     * Get name of a MethodNode node,
     * e.g. this.run(), get "run"
     * @param nodeTnwp : MethodNode node
     * @return name of a MethodNode node
     */
    String getTnwpName(TreeNodeWithProperties nodeTnwp) {
        if (nodeTnwp == null) {
            return null
        }
        return nodeTnwp.getPropertyValue("name")
    }

    /**
     * Get raw text of a TreeNodeWithProperty node
     * e.g. log.debug(Turning switch ON)
     * @param nodeTnwp : TreeNodeWithProperty node
     * @return raw text of TreeNodeWithProperty node
     */
    String getTnwpText(TreeNodeWithProperties nodeTnwp) {
        if (nodeTnwp == null) {
            return null
        }
        return nodeTnwp.getPropertyValue("text")
    }

    /**
     * Get class name of a TreeNodeWithProperty node,
     * e.g. class org.codehaus.groovy.ast.expr.MethodCallExpression
     * @param nodeTnwp : TreeNodeWithProperty node
     * @return class name of TreeNodeWithProperty node
     */
    String getTnwpClass(TreeNodeWithProperties nodeTnwp) {
        if (nodeTnwp == null) {
            return null
        }
        return nodeTnwp.getPropertyValue("class")
    }

    /**
     * Get method call expression name from MethodCallExpression
     * e.g. log.debug(), get "debug"
     * @param nodeTnwp : MethodCallExpression node
     * @return method call expression name
     */
    String getTnwpMethodAsString(TreeNodeWithProperties nodeTnwp) {
        if (nodeTnwp == null) {
            return null
        }
        return nodeTnwp.getPropertyValue("methodAsString")
    }

    /**
     * Write json map into file
     * @param fileNameStr : file name
     * @param jsonMap : json map
     */
    static void writeToJsonFile(String fileNameStr, Map jsonMap) {
        String jsonStr = JsonOutput.toJson(jsonMap)
        String jsonPrettyStr = JsonOutput.prettyPrint(jsonStr)
        File jsonFile = new File(fileNameStr)
        jsonFile.write(jsonPrettyStr)
    }
}
