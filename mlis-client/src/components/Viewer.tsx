import * as React from 'react';
import { createFragmentContainer, RelayProp } from 'react-relay';
import { graphql } from 'babel-plugin-relay/macro';

import { Viewer_viewer } from './__generated__/Viewer_viewer.graphql';
import { Navbar, NavItem, Nav } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import LogoutMutation from '../mutations/LogoutMutation';
import { LinkContainer } from 'react-router-bootstrap';

interface Props {
  relay: RelayProp
  viewer: Viewer_viewer
  onLogout: any
}

class Viewer extends React.Component<Props> {
  render() {
    return (
      <Navbar>
        <Navbar.Header>
          <Navbar.Brand>
            <Link to="/">MLIS</Link>
          </Navbar.Brand>
          <Navbar.Toggle />
        </Navbar.Header>
        <Navbar.Collapse>
          <Nav pullRight>
            <LinkContainer to="/classes">
              <NavItem>Classes</NavItem>
            </LinkContainer>
            <LinkContainer to="/ranking">
              <NavItem>Ranking</NavItem>
            </LinkContainer>
            <LinkContainer to={`/user/${this.props.viewer.user.id}`}>
              <NavItem>
                {this.props.viewer.user.name}
              </NavItem>
            </LinkContainer>
            <NavItem onClick={() => {
                    LogoutMutation.commit(
                      this.props.onLogout
                    );
                  }}>
              Logout
            </NavItem>
          </Nav>
        </Navbar.Collapse>
      </Navbar>
    );
  }
}

export default createFragmentContainer(Viewer, {
  viewer: graphql`
    fragment Viewer_viewer on Viewer {
      user {
        id
        name
      }
    }
  `,
});