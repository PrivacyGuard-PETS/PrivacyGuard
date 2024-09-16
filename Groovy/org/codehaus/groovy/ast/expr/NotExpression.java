package org.codehaus.groovy.ast.expr;

import org.codehaus.groovy.ast.GroovyCodeVisitor;

public class NotExpression extends BooleanExpression {
    public NotExpression(Expression expression) {
        super(expression);
    }

    public void visit(GroovyCodeVisitor visitor) {
        visitor.visitNotExpression(this);
    }

    public boolean isDynamic() {
        return false;
    }

    public Expression transformExpression(ExpressionTransformer transformer) {
        Expression ret = new NotExpression(transformer.transform(this.getExpression()));
        ret.setSourcePosition(this);
        ret.copyNodeMetaData(this);
        return ret;
    }

    public String getText() {
        return "!"+super.getText();
    }
}
